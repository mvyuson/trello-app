from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.views.generic.dates import ArchiveIndexView
from trello.views import (
        SignUpView, 
        LoginView,
        DashBoardView,
        LogoutView,
        BoardView,
        CreateBoardView,
        AddCardView,
        CardDescriptionView,
        UpdateBoard,
        UpdateListView,
        DeleteBoardView,
        DeleteCardView,
        DeleteListView,
        ArchiveView,
        BoardArchiveView,
        ListArchiveView,
        CardArchiveView,
        InviteMemberView,

)
from .models import Board
from django.urls import path

urlpatterns = [  
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('password_reset/', auth_views.password_reset, name='password_reset'),
    path('password_reset_done/', auth_views.password_reset_done, name='password_reset_done'),
    path('reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', auth_views.password_reset_complete, name='password_reset_complete'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('dashboard/', DashBoardView.as_view(), name='dashboard'),
    path('create-board/', CreateBoardView.as_view(), name='create-board'),
    path('board/<int:id>/', BoardView.as_view(), name='board'),
    path('board/<int:id>/list/', AddCardView.as_view(), name='add_card'),
    path('description/<int:id>/', CardDescriptionView.as_view(), name='description'),

    path('board/<int:id>/edit-board/', UpdateBoard.as_view(), name='edit-board'),
    path('board/<int:id>/edit-list/', UpdateListView.as_view(), name='edit-list'),

    path('board/<int:id>/delete-board/', DeleteBoardView.as_view(), name='delete-board'),
    path('delete-list/<int:id>/', DeleteListView.as_view(), name='delete-list'),
    path('delete-card/<int:id>/', DeleteCardView.as_view(), name='delete-card'),

    path('archive/', ArchiveView.as_view(), name='archive'),
    path('board-archive/<int:id>/', BoardArchiveView.as_view(), name='board-archive'),
    path('list-archive/<int:id>/', ListArchiveView.as_view(), name='list-archive'),
    path('card-archive/<int:id>/,', CardArchiveView.as_view(), name='card-archive'),

    path('invite-member/<int:id>/', InviteMemberView.as_view(), name='invite-member'),
]