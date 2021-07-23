from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse, resolve
from ..models import Board, Topic, Post
from ..views import reply_topic
from ..forms import PostForm


class ReplyTopicTestCase(TestCase):
    '''
    Base case for 'reply_topic' view tests
    '''
    def setUp(self, data={}):
        self.board = Board.objects.create(name='Django', description='Django board.')
        self.username = 'john'
        self.password = '123'
        user = User.objects.create_user(username=self.username, email='johndoe@noemail.com', password=self.password)
        self.topic = Topic.objects.create(subject='Hello world', board=self.board, starter=user)
        Post.objects.create(message='Lorem ipsum dolor sit amet', topic=self.topic, created_by=user)
        self.url = reverse('reply_topic', kwargs={'pk':self.board.id, 'topic_pk':self.topic.id})
        
    
class LoginRequiredReplyTopicTests(ReplyTopicTestCase):
    '''
    User not logged in
    '''
    def test_redirection_to_login(self):
        login_url = reverse('login')
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{login_url}?next={self.url}')
    
    
class ReplyTopicTests(ReplyTopicTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.get(self.url)
        
    def test_status_code(self):
        self.assertEquals(self.response.status_code, 200)
        
    def test_view_function(self):
        view = resolve('/boards/{pk}/topics/{topic_pk}/reply/'.format(pk=self.board.id, topic_pk=self.topic.id))
        self.assertEquals(view.func, reply_topic)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')
    
    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, PostForm)
        
    def test_form_inputs(self):
        '''
        View must contain inputs: csrf, message textarea
        '''
        self.assertContains(self.response, '<input', 1)
        self.assertContains(self.response, '<textarea', 1)
        
        
class SuccessfulReplyTopicTests(ReplyTopicTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {'message': 'test message post'})
        
    def test_redirection(self):
        url = reverse('topic_posts', kwargs={'pk':self.board.id, 'topic_pk':self.topic.id})
        topic_post_url = '{url}?page=1#2'.format(url=url)
        self.assertRedirects(self.response, topic_post_url)
        
    def test_reply_created(self):
        '''
        Two posts exist: 'ReplyTopicTestCase' setUp and SuccessfulReplyTopicTests setUp
        '''
        self.assertEquals(Post.objects.count(), 2)
        
    
class InvalidReplyTopicTests(ReplyTopicTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {})
        
    def test_status_code(self):
        '''
        Invalid form submission returns to same page
        '''
        self.assertEquals(self.response.status_code, 200)
        
    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)
