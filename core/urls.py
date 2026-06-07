from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('programs/', views.programs, name='programs'),
    path('programs/<slug:slug>/', views.program_detail, name='program_detail'),
    path('admissions/', views.admissions, name='admissions'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('apply/', views.apply, name='apply'),
    #    path('admissions/', views.admissions, name='admissions'),
    path('admissions/tuition/', views.admissions_tuition, name='admissions_tuition'),
    path('admissions/financial-aid/', views.admissions_financial_aid, name='admissions_financial_aid'),
    path('admissions/requirements/', views.admissions_requirements, name='admissions_requirements'),
    path('admissions/faq/', views.admissions_faq, name='admissions_faq'),
    path('about/mission/', views.about_mission, name='about_mission'),
    path('about/team/', views.about_team, name='about_team'),
    path('about/accreditations/', views.about_accreditations, name='about_accreditations'),
    path('about/careers/', views.about_careers, name='about_careers'),
]
