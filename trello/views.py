from django.views.generic.edit import DeleteView, UpdateView
from django.views.generic import TemplateView, RedirectView, View
from django.template.loader import render_to_string
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.conf import settings


from .forms import (
    SignUpForm, 
    LoginForm, 
    AddBoardTitleForm, 
    AddListForm, 
    CardImageForm,
    UserProfileForm,
    EditUserForm,
    EditCardTitleForm,
)

from .models import (
    Card, 
    List, 
    Board, 
    BoardMembers, 
    BoardInvite,  
    UserProfile
)

import json


"""
REMINDER: THE APP MUST NOT ACCEPT AND RETURN BLANK VALUES WHEN UPDATING.
          UPDATE CARD AND CREATE CARD DESCRIPTION MUST HAVE THE SAME VIEW
          FUNCTION.
"""

class SignUpView(TemplateView):
    """
    View for the signup.
    """

    form = SignUpForm
    template_name = 'trello/signup.html'

    """
    Render form to signup page.
    """

    def get(self, *args, **kwargs):
        form = SignUpForm()
        context = {'form':form}
        return render(self.request, self.template_name, context)

    """
    If form is validated, the user will be redirected to login page.
    If not, form will be rerendered.
    """

    def post(self, *args, **kwargs):
        form = self.form(self.request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        context = {'form':form}
        return render(self.request, self.template_name, context)


class LoginView(TemplateView):
    """
    View for login.
    """
    
    form = LoginForm
    template_name = 'trello/login.html'

    """
    Render login form to login page.
    """
    
    def get(self, *args, **kwargs):
        form = LoginForm()
        context = {'form':form}
        return render(self.request, self.template_name, context)

    """
    Assign username and password with the values retrieved from form.
    If form is valid after validating, django will authenticate user
    by comparing the data entered vs data registered in the database.
    If user credentials have a matching values from the database, the 
    user will turn as active and will be redirected to the dashboard.
    Else the method will rerender the form.
    """

    def post(self, *args, **kwargs):
        form = self.form(self.request.POST)
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')
        context = {'form':form}
        if form.is_valid():
            user = authenticate(self.request, username=username, password=password)
            if user is not None:
                login(self.request, user)
                return redirect('dashboard') 
            else:
                return render(self.request, self.template_name, context)
        return render(self.request, self.template_name, context)


class LogoutView(RedirectView):
    """
    Logout User
    """

    def get(self, *args, **kwargs):
        logout(self.request)
        return redirect('login')


class DashBoardView(LoginRequiredMixin, TemplateView):
    """
    Display all the boards made by the user.
    Render Add Board form.
    """
    
    login_url = '/login/'
    template_name = 'trello/list.html'
    form = AddBoardTitleForm

    def get(self, *args, **kwargs):
        board = Board.objects.filter(author=self.request.user, archived=False).order_by('id')
        board_member = BoardMembers.objects.filter(members=self.request.user).order_by('id')
        board_owner = BoardMembers.objects.filter(owner=True)
        context = {'board':board, 'board_member':board_member, 'board_owner':board_owner}
        return render(self.request, self.template_name, context)
 

class CreateBoardView(LoginRequiredMixin, TemplateView):
    """
    When 'Create Board' is clicked, add board form will render.
    Redirect to board with the saved board title.
    """

    template_name = 'trello/create-board.html' 
    form = AddBoardTitleForm

    def get(self, *args, **kwargs):
        form = self.form()
        return render(self.request, self.template_name,  {'form':form})

    """
    If form is valid, form.save(commit=False). It indicates that don't 
    save the form yet because the author of the board which is the current 
    user of the page was have not been set yet. After the board author has 
    been assigned, the form will be save. Then return a JsonResponse with 
    board as argument.

    If form is not valid, this view will return an error 400 which indicates 
    that the server can't process sent by the user may be due to invalid syntax 
    or attempting on submitting the form with empty values.
    """

    def post(self, *args, **kwargs):
        form = self.form(self.request.POST)
        if form.is_valid():
            board = form.save(commit=False)
            board.author = self.request.user
            board.save()
            BoardMembers.objects.create(board=board, members=self.request.user, owner=True)
            return JsonResponse({'board':board.id})    
        else:
            return HttpResponse(status=400)
        return render(self.request, self.template_name,  {'form':form})


class BoardView(LoginRequiredMixin, TemplateView):
    """
    Display the board details by returning the board, board_members, and other forms to the template.
    Get the current Board and save the newly added list
    """

    template_name = 'trello/board.html'
    form = AddListForm
    board_form = AddBoardTitleForm

    def get(self, *args, **kwargs):
        """
        Get the kwargs of board_list
        """

        form = self.form()
        board = get_object_or_404(Board, id=kwargs.get("id")) 
        board_members = BoardMembers.objects.filter(board=board).order_by('id')
        board_form = self.board_form(self.request.POST, instance=board)
        context = {'board':board, 'board_members':board_members, 'form':form, 'board_form':board_form}
        return render(self.request, self.template_name, context)    

    def post(self, *args, **kwargs):
        form = self.form(self.request.POST)
        if form.is_valid():
            board_list = form.save(commit=False)
            board_list.board = get_object_or_404(Board, id=kwargs.get('id'))
            board_list.author = self.request.user
            board_list.save()
            return JsonResponse({'board_list':board_list.list_title, 'id':board_list.id})
        else: 
            return HttpResponse(status=400)
        return render(self.request, self.template_name, {'form':form})


class AddCardView(LoginRequiredMixin, TemplateView):
    """
    Add a newly created card.
    card_list gets the id of the current List
    title gets the newly added card

    """

    def post(self, request, *args, **kwargs):
        card_list = get_object_or_404(List, id=kwargs.get('id'))
        title = self.request.POST.get('card_title')
        card = Card.objects.create(card_title=title, board_list=card_list, author=self.request.user)
        return JsonResponse({'card':card.card_title, 'id':card.id})


class CardDescriptionView(LoginRequiredMixin, TemplateView):
    """
    Blockers: Returns an empty card_title when its only description that is being updated.

    Display the card detail of a card inside the modal.
    """

    template_name = 'trello/description.html'
    form = CardImageForm
    title_form = EditCardTitleForm

    def get(self, *args, **kwargs):
        card = get_object_or_404(Card, id=kwargs.get('id'))
        form = self.form()
        title_form = self.title_form(instance=card)
        context = {'form':form, 'title_form':title_form, 'card':card}
        return render(self.request, self.template_name, context)

    def post(self, *args, **kwargs):
        #import pdb; pdb.set_trace()
        card = get_object_or_404(Card, id=kwargs.get('id'))
        title_form = self.title_form(self.request.POST, instance=card)

        if title_form.is_valid():
            update_card = title_form.save(commit=False)
           
            if update_card.card_title is None:
                update_card.card_title = card.card_title
                print('WALA')

            print(card.card_title)
            update_card.author = self.request.user 
            update_card.board_list = card.board_list 
            update_card.save()
            return JsonResponse({'card': update_card.card_title, 'id': update_card.id, 'card_description': update_card.card_description, 'board': update_card.board_list.board.id})
        return render(self.request, self.template_name, {'form':title_form})


class CardDragAndDropView(LoginRequiredMixin, View):
    """
    Drag and drop card to a list and update it's list.
    1. Get the value of the dragged and dropped card, and the value of 
       the list it was dropped.
    2. Set the new list value of card with the value of the list it was
       dropped.
    3. Save.
    """

    def post (self, *args, **kwargs):
        drop_list = self.request.POST.get('blist')
        card = self.request.POST.get('card')
        current_card = Card.objects.get(id=card)
        current_list = List.objects.get(id=drop_list)
        current_card.board_list = current_list
        current_card.save()
        return JsonResponse({'card':current_card.id})


class UpdateBoard(LoginRequiredMixin, TemplateView):
    """
    Update the value of the board title.
    1. Get the new value of the current board.
    2. Update the new value of the current board
    """

    def post(self, *args, **kwargs):
        board = get_object_or_404(Board, id=kwargs.get('id'))
        update_board = self.request.POST.get('board_title') 
        current_board = Board.objects.get(id=board.id)
        current_board.title = update_board 
        current_board.save()
        return JsonResponse({'board':current_board.title})


class UpdateListView(LoginRequiredMixin, TemplateView):
    """
    Update the value of the list title.
    1. Get the new list value from the frontend.
    2. Get the id of the edited list.
    3. Get the id passed by the url
    4. Update List and save.
    """

    def post(self, *args, **kwargs):
        edit_list = self.request.POST.get('list_data')     
        list_id = self.request.POST.get('list_id')      
        update_list = List.objects.get(id=list_id)
        update_list.list_title = edit_list
        update_list.save()
        return JsonResponse({'board_list':update_list.id})


class DeleteBoardView(LoginRequiredMixin, DeleteView):
    """
    Delete the current Board.
    """
    
    def get(self, *args, **kwargs):
        board_to_delete = get_object_or_404(Board, id=kwargs.get('id'))
        board_to_delete.delete()
        return redirect('dashboard')


class DeleteListView(LoginRequiredMixin, DeleteView):
    """
    Delete the current List.
    """
    
    def get(self, *args, **kwargs):
        list_to_delete = get_object_or_404(List, id=kwargs.get('id'))
        board = list_to_delete.board.id
        list_to_delete.delete()
        return redirect('board', board)


class DeleteCardView(LoginRequiredMixin, DeleteView):
    """
    Delete the current Card.
    """

    def get(self, *args, **kwargs):
        card_to_delete = get_object_or_404(Card, id=kwargs.get('id'))
        card_to_delete.delete()
        return redirect('board', card_to_delete.board_list.board.id )


class BoardArchiveView(LoginRequiredMixin, View):
    """
    Archive Board by setting its archived field into True.
    """

    def get(self, *args, **kwargs):
        board = get_object_or_404(Board, id=kwargs.get('id'))
        board.archived = True 
        board.save()
        return JsonResponse({'board':board.id})


class RestoreArchivedBoard(LoginRequiredMixin, View):
    """
    Restore Archived Board
    """

    def get(self, *args, **kwargs):
        board = get_object_or_404(Board, id=kwargs.get('id'))
        board.archived = False 
        board.save()
        return redirect('dashboard')


class RestoreArchivedList(LoginRequiredMixin, View):
    """
    Restore Archived List
    """

    def get(self, *args, **kwargs):
        board_list = get_object_or_404(List, id=kwargs.get('id'))
        board_list.archived = False
        board_list.save()
        return redirect('board', board_list.board.id)


class RestoreArchivedCard(LoginRequiredMixin, View):
    """
    Restore Archived Card
    """

    def get(self, *args, **kwargs):
        card = get_object_or_404(Card, id=kwargs.get('id'))
        card.archived = False 
        card.save()
        return redirect('board', card.board_list.board.id)


class ListArchiveView(LoginRequiredMixin, View):
    """
    Archive List by setting its archived field into True.
    """

    def get(self, *args, **kwargs):
        board_list = get_object_or_404(List, id=kwargs.get('id'))
        board_list.archived = True 
        board_list.save()
        return JsonResponse({'board':board_list.board.id})


class CardArchiveView(LoginRequiredMixin, View):
    """
    Archive Card by setting its archived field into True.
    """

    def get(self, *args, **kwargs):
        card = get_object_or_404(Card, id=kwargs.get('id'))
        card.archived = True 
        card.save()
        return JsonResponse({'board':card.board_list.board.id})


class ArchiveView(LoginRequiredMixin, TemplateView):
    """
    Display the archive boards, lists, and cards in one template order by the date it was created.
    1. Get all the boards with the current user as the author, and if archived is equal to true, order
       by the date it was created.
    2. Get all the lists with the current user as the author, and if archived is equal to true, order
       by the date it was created.
    3. Get all the cards with the current user as the author, and if archived is equal to true, order
       by the date it was created.
    """

    template_name = 'trello/board_archive.html'

    def get(self, *args, **kwargs):
        archive_boards = Board.objects.filter(author=self.request.user, archived=True).order_by('created_date')
        archive_list = List.objects.filter(author=self.request.user, archived=True).order_by('created_date')
        archive_card = Card.objects.filter(author=self.request.user, archived=True).order_by('created_date')
        context = {'archive_boards':archive_boards, 'archive_list':archive_list, 'archive_card':archive_card}
        return render(self.request, self.template_name, context)


class InviteMemberView(LoginRequiredMixin, TemplateView):
    """
    NOT UPDATED

    Invite other user as a member of the board. The user will enter the username of the member
    and submit it. Then activate its membership. Then set the current user as the owner of the 
    board. Then redirect it to Board Details.

    REMINDER: Convert it into AJAX 
    """

    template_name = 'trello/board.html'

    def send_email_msg(self, message, to_email):
        send_mail(
            'Invite Member',
            message,
            settings.EMAIL_HOST_USER,
            [to_email],
        )

    def post(self, *args, **kwargs):
        member_email = self.request.POST.get('member_email')
        board = get_object_or_404(Board, id=kwargs.get('id'))
        invite_by = self.request.user.username
        member = User.objects.filter(email=member_email)

        if member.exists():
            message = 'You are invited by {} to join board {}. Click the link below to join. http://3b8b75b8.ngrok.io/dashboard'.format(invite_by, board.title)
            self.send_email_msg(message, member_email)

            current_member = User.objects.get(email=member_email)
            new_board_member = BoardMembers.objects.create(board=board, members=current_member)

            return redirect('board', board.id)
        else:
            message = 'You are invited by {} to join board {}. Click the link below to join. http://3b8b75b8.ngrok.io/register'.format(invite_by, board.title)
            self.send_email_msg(message, member_email)
            
            initial_member = BoardInvite.objects.create(board=board, email_member=member_email)

            return redirect('board', board.id)


class RegisterInvitedUser(LoginRequiredMixin, View):
    """
    NOT UPDATED
    """


    form = SignUpForm
    template_name = "trello/register_invited_user.html"

    def get(self, *args, **kwargs):
        form = self.form()
        return render(self.request, self.template_name, {'form':form})

    def post(self, *args, **kwargs):
        #import pdb; pdb.set_trace()
        form = self.form(self.request.POST)
        if form.is_valid():
            form.save(commit=False)
            member_email = self.request.POST.get('email')
            email = BoardInvite.objects.filter(email_member=member_email)

            if email.exists():
                form.save()
                new_member = BoardInvite.objects.get(email_member=member_email)
                board = Board.objects.get(id=new_member.board.id)
                user = User.objects.get(email=member_email)

                new_board_member = BoardMembers.objects.create(board=board, members=user, deactivate=False, owner=False)
                new_board_member.save()

                print('Success')
                return redirect('login')
            else:
                print('Fail')
                return HttpResponse(status=400)
        form = SignUpForm()
        return render(self.request, self.template_name, {'form':form})
        

class LeaveBoardView(LoginRequiredMixin, View):
    """
    Let the user who is a member of the board to leave by setting the deactivating its membership.
    """

    def get(self, *args, **kwargs):
        print(self.request.user)
        board = get_object_or_404(Board, id=kwargs.get('id'))
        board_member = BoardMembers.objects.get(board=board, members=self.request.user)
        board_member.deactivate = True
        board_member.save()
        return redirect('dashboard')


class EditUserProfile(LoginRequiredMixin, TemplateView):
    """
    Add bio and edit user profile 
    """
    
    template_name = 'trello/user_profile.html'
    user_form = EditUserForm
    user_profile_form = UserProfileForm

    def get(self, *args, **kwargs):
        user_form = self.user_form(instance=self.request.user)
        user_profile_form = self.user_profile_form(instance=self.request.user.userprofile)
        context = {'userprofile':self.request.user, 'user_form':user_form, 'user_profile_form':user_profile_form}
        return render(self.request, self.template_name, context)

    def post(self, *args, **kwargs):
        user_form = self.user_form(self.request.POST, instance=self.request.user)
        user_profile_form = self.user_profile_form(self.request.POST, instance=self.request.user.userprofile)        

        if user_form.is_valid() or user_profile_form.is_valid():
            user = user_form.save()
            user_profile = user_profile_form.save(commit=False)
            user_profile.user = user
            user_profile.save()
            return redirect('user-profile')
        return render(self.request, self.template_name, {'user_form':user_form, 'user_profile_form':user_profile_form})


class DeleteCardCoverImage(LoginRequiredMixin, DeleteView):
    """
    Delete Card Image
    """
    
    def get(self, *args, **kwargs):
        card = get_object_or_404(Card, id=kwargs.get('id'))
        card.image = None
        card.save()
        return JsonResponse({'card':card.id})


class UploadImageView(LoginRequiredMixin, View):
    """
    Upload Card Image
    """
    
    template_name = 'trello/description.html'
    form = CardImageForm

    def post(self, *args, **kwargs):
        parent_card = get_object_or_404(Card, id=kwargs.get('id'))
        form = self.form(self.request.POST, self.request.FILES, instance=parent_card)

        if form.is_valid():
           new_image = form.save(commit=False)
           new_image.author = self.request.user
           new_image.board_list = parent_card.board_list
           new_image.save()
           return redirect('board', parent_card.board_list.board.id)
        return render(self.request, self.template_name, {'form':form})
