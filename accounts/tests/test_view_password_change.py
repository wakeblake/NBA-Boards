from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.test import TestCase


class PasswordChangeTests(TestCase):
    '''
    User logged in
    '''
    def setUp(self):
        username = 'john'
        password = 'abcde12345'
        user = User.objects.create_user(username=username, email='johndoe@noemail.com', password=password)
        url = reverse('password_change')
        self.client.login(username=username, password=password)
        self.response = self.client.get(url)
        
    def test_status_code(self):
        self.assertEquals(self.response.status_code, 200)
        
    def test_url_resolves_correct_view(self):
        view = resolve('/settings/password/')
        self.assertEquals(view.func.view_class, auth_views.PasswordChangeView)
        
    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')
        
    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, PasswordChangeForm)
        
    def test_form_inputs(self):
        '''
        View must contain inputs: csrf, old_password, new_password, new_password2
        '''
        self.assertContains(self.response, '<input', 4)
        self.assertContains(self.response, 'type="password"', 3)
    
    
class LoginRequiredPasswordChangeTests(TestCase):
    '''
    User not logged in
    '''
    def test_redirection_to_login(self):
        url = reverse('password_change')
        login_url = reverse('login')
        response = self.client.get(url)
        self.assertRedirects(response, f'{login_url}?next={url}')
        
        
class PasswordChangeTestCase(TestCase):
    '''
    Useful to test successful and invalid password changes - accepts 'data' to POST to view
    '''
    def setUp(self, data={}):
        self.user = User.objects.create_user(username='john', email='johndoe@noemail.com', password='old_password')
        self.url = reverse('password_change')
        self.client.login(username='john', password='old_password')
        self.response = self.client.post(self.url, data)

        
class SuccessfulPasswordChangeTests(PasswordChangeTestCase):
    def setUp(self):
        super().setUp({
            'old_password': 'old_password',
            'new_password1': 'new_password',
            'new_password2': 'new_password',
        })
    
    def test_redirection(self):
        self.assertRedirects(self.response, reverse('password_change_done'))
        
    def test_password_changed(self):
        '''
        Refreshes user instance from db to get new password
        '''
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new_password'))
        
    def test_user_authentication(self):
        '''
        Response from request to new page after successful pw change should indicate user authenticated
        '''
        response = self.client.get(reverse('home'))
        user = response.context.get('user')
        self.assertTrue(user.is_authenticated)
    
class InvalidPasswordChangeTests(PasswordChangeTestCase):
    def test_status_code(self):
        '''
        Invalid form submission returns to same page
        '''
        self.assertEquals(self.response.status_code, 200)
        
    def test_form_errors(self):
        form = self.response.context.get('form')
        self.assertTrue(form.errors)

    def test_didnt_change_password(self):
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('old_password'))
    