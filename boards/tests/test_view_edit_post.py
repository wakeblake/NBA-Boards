from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse, resolve
from django.forms import ModelForm
from ..models import Board, Post, Topic
from ..views import PostUpdateView


class PostUpdateViewTestCase(TestCase):
    '''
    Base test case for all 'PostUpdateView' view tests
    '''
    def setUp(self):
        self.board = Board.objects.create(name='Django', description='django board')
        self.username = 'john'
        self.password = '123'
        user = User.objects.create_user(username=self.username, email='johndoe@noemail.com', password=self.password)
        self.topic = Topic.objects.create(subject='Hello, world!', board=self.board, starter=user)
        self.post = Post.objects.create(message='Lorem ipsum dolor sit amet', topic=self.topic, created_by=user)
        self.url = reverse('edit_post', kwargs={
            'pk':self.board.id,
            'topic_pk':self.topic.id,
            'post_pk':self.post.pk
        })
        
        
class LoginRequiredPostUpdateViewTests(PostUpdateViewTestCase):
    def test_redirection(self):
        '''
        Users must be logged in
        '''
        login_url = reverse('login')
        response = self.client.get(self.url)
        self.assertRedirects(response, '{login_url}?next={url}'.format(login_url=login_url, url=self.url))
        

class UnauthorizedPostUpdateViewTests(PostUpdateViewTestCase):
    def setUp(self):
        '''Create new user'''
        super().setUp()
        username='jane'
        password='321'
        user = User.objects.create_user(username=username, email='janedoe@noemail.com', password=password)
        self.client.login(username=username, password=password)
        self.response = self.client.get(self.url)
        
    def test_status_code(self):
        '''
        Unauthorized new user receives 404 response
        '''
        self.assertEquals(self.response.status_code, 404)
        
    
class PostUpdateViewTests(PostUpdateViewTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.get(self.url)
    
    def test_status_code(self):
        self.assertEquals(self.response.status_code, 200)
    
    def test_view_function(self):
        view = resolve('/boards/{pk}/topics/{topic_pk}/posts/{post_pk}/edit/'.format(pk=self.board.id, topic_pk=self.topic.id, post_pk=self.post.id))
        self.assertEquals(view.func.view_class, PostUpdateView)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')
    
    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, ModelForm)
        
    def test_form_inputs(self):
        '''
        View must contain inputs: csrf, message textarea
        '''
        self.assertContains(self.response, '<input', 1)
        self.assertContains(self.response, '<textarea', 1)
        
        
class SuccessfulPostUpdateViewTests(PostUpdateViewTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {'message': 'changed the post'})
        
    def test_redirection(self):
        topic_post_url = reverse('topic_posts', kwargs={'pk':self.board.id, 'topic_pk':self.topic.id})
        self.assertRedirects(self.response, topic_post_url)
        
    def test_OP_edited(self):
        '''
        One post exists with message 'changed the post'
        '''
        self.post.refresh_from_db()
        self.assertEquals(self.post.message, 'changed the post')
        

class InvalidPostUpdateViewTests(PostUpdateViewTestCase):
    def setUp(self):
        '''
        Submit an empty dictionary to edit_post
        '''
        super().setUp()
        self.client.login(username=self.username, password=self.password)
        self.response = self.client.post(self.url, {})
        
    def test_status_code(self):
        '''
        Invalid form returns to same page
        '''
        self.assertEquals(self.response.status_code, 200)
        
    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)