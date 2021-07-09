from celery import shared_task
from friendships.services import FriendshipService
from newsfeeds.constants import FANOUT_BATCH_SIZE
from newsfeeds.models import NewsFeed
from testing.testcases import TestCase
from tweets.models import Tweet
from utils.time_constants import ONE_HOUR


@shared_task(routing_key='newsfeeds', time_limit=ONE_HOUR)
def fanout_newsfeeds_batch_task(tweet_id, follower_ids):
    # import 写在里面避免循环依赖
    from newsfeeds.services import NewsFeedService

    # 错误的方法：将数据库操作放在 for 循环里面，效率会非常低 ->
    # for follower_id in follower_ids:
    #     NewsFeed.objects.create(user_id=follower_id, tweet_id=tweet_id)
    # 正确的方法：使用 bulk_create，会把 insert 语句合成一条 ->
    newsfeeds = [
        NewsFeed(user_id=follower_id, tweet_id=tweet_id)
        for follower_id in follower_ids
    ]

    NewsFeed.objects.bulk_create(newsfeeds)

    # bulk create 不会触发 post_save 的 signal，所以需要手动 push 到 cache 里
    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)

    return "{} newsfeeds created".format(len(newsfeeds))


@shared_task(routing_key='default', time_limit=ONE_HOUR)
def fanout_newsfeeds_main_task(tweet_id, tweet_user_id):
    # 将推给自己的 Newsfeed 率先创建，确保自己能最快看到
    NewsFeed.objects.create(user_id=tweet_user_id, tweet_id=tweet_id)

    # 获得所有的 follower ids，按照 batch size 拆分开
    follower_ids = FriendshipService.get_follower_ids(tweet_user_id)
    index = 0
    while index < len(follower_ids):
        batch_ids = follower_ids[index: index + FANOUT_BATCH_SIZE]
        fanout_newsfeeds_batch_task.delay(tweet_id, batch_ids)
        index += FANOUT_BATCH_SIZE

    return '{} newsfeeds going to fanout, {} batches created.'.format(
        len(follower_ids),
        (len(follower_ids) - 1) // FANOUT_BATCH_SIZE + 1,
    )


class NewsFeedTaskTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.linghu = self.create_user('linghu')
        self.dongxie = self.create_user('dongxie')

    def test_fanout_main_task(self):
        tweet = self.create_tweet(self.linghu, 'tweet 1')
        self.create_friendship(self.dongxie, self.linghu)
        msg = fanout_newsfeeds_main_task(tweet.id, self.linghu.id)
        self.assertEqual(msg, '1 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(1 + 1, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_list), 1)

        for i in range(2):
            user = self.create_user('user{}'.format(i))
            self.create_friendship(user, self.linghu)
        tweet = self.create_tweet(self.linghu, 'tweet 2')
        msg = fanout_newsfeeds_main_task(tweet.id, self.linghu.id)
        self.assertEqual(msg, '3 newsfeeds going to fanout, 1 batches created.')
        self.assertEqual(4 + 2, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_list), 2)

        user = self.create_user('another user')
        self.create_friendship(user, self.linghu)
        tweet = self.create_tweet(self.linghu, 'tweet 3')
        msg = fanout_newsfeeds_main_task(tweet.id, self.linghu.id)
        self.assertEqual(msg, '4 newsfeeds going to fanout, 2 batches created.')
        self.assertEqual(8 + 3, NewsFeed.objects.count())
        cached_list = NewsFeedService.get_cached_newsfeeds(self.linghu.id)
        self.assertEqual(len(cached_list), 3)
        cached_list = NewsFeedService.get_cached_newsfeeds(self.dongxie.id)
        self.assertEqual(len(cached_list), 3)