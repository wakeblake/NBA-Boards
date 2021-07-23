from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views.generic import View, CreateView, UpdateView, ListView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Board, Topic, Post
from .forms import NewTopicForm, PostForm


# Create your views here.
def home(request):
    boards = Board.objects.all()
    return render(request, 'home.html', {'boards': boards})

def board_topics(request, pk):
    '''
    Paginate a function-based view
    '''
    board = get_object_or_404(Board, id=pk)
    queryset = board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
    page = request.GET.get('page', 1)
    
    paginator = Paginator(queryset, 10)
    
    try:
        topics = paginator.page(page)
    except PageNotAnInteger:
        topics = paginator.page(1)
    except EmptyPage:
        topics = paginator.page(paginator.num_pages)
        
    return render(request, 'topics.html', {'board': board, 'topics':topics})

@login_required
def new_topic(request, pk):
    board = get_object_or_404(Board, id=pk)
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.starter = request.user
            topic.save()
            post = Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                created_by=request.user
            )
            return redirect('topic_posts', pk=board.id, topic_pk=topic.id)
    else:
        form = NewTopicForm()
        
    return render(request, 'new_topic.html', {'board':board, 'form':form})

@login_required
def reply_topic(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board_id=pk, id=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()
            
            topic.last_updated = timezone.now()
            topic.save()
            
            topic_url = reverse('topic_posts', kwargs={'pk':pk, 'topic_pk':topic_pk})
            topic_post_url = '{url}?page={page}#{id}'.format(
                url=topic_url,
                id=post.id,
                page=topic.get_page_count()
            )
            
            return redirect(topic_post_url)
    else:
        form = PostForm()
        
    return render(request, 'reply_topic.html', {'topic':topic, 'form':form})


class PostListView(ListView):
    '''
    Paginate a class-based view
    '''
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_posts.html'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        session_key = 'viewed_topic_{}'.format(self.topic.id)
        if not self.request.session.get(session_key, False):
            self.topic.views += 1
            self.topic.save()
            self.request.session[session_key] = True
        kwargs['topic'] = self.topic
        return super().get_context_data(**kwargs)
    
    def get_queryset(self):
        self.topic = get_object_or_404(Topic, board_id=self.kwargs.get('pk'), id=self.kwargs.get('topic_pk'))
        queryset = self.topic.posts.order_by('created_at')
        return queryset
    
    
class NewPostView(View):
    '''
    Example of a Class-Based View
    '''
    def render(self, request):
        return render(request, 'new_post.html', {'form': self.form})
    
    def post(self, request):
        self.form = PostForm(request.POST)
        if self.form.is_valid():
            self.form.save()
            return redirect('post_list')
        return self.render(request)
    
    def get(self, request):
        self.form = PostForm()
        return self.render(request)


@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    '''
    Example of a Generic Class-Based View - 
    (CreateView, DeleteView, DetailView, FormView, UpdateView, ListView)
    '''
    model = Post
    fields = ('message', )
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)
    
    def form_valid(self, form):
        '''
        Overriding form_valid() to add extra fields
        '''
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()
        return redirect('topic_posts', pk=post.topic.board.id, topic_pk=post.topic.id)