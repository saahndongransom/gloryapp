from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chatbot_response, name='chatbot_response'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('programs/', views.programs, name='programs'),
    path('programs/<slug:slug>/', views.program_detail, name='program_detail'),
    path('admissions/', views.admissions, name='admissions'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('apply/', views.apply, name='apply'),
    path('apply/cna/', views.apply_cna, name='apply_cna'),
    path('apply/cna/fill/', views.fill_pdf_cna, name='fill_pdf_cna'),
    path('apply/cna/form/', views.fill_form_cna, name='fill_form_cna'),
    path('apply/cna/submit-form/', views.submit_form_cna, name='submit_form_cna'),
    path('apply/cna/render-page/', views.render_pdf_page, name='render_pdf_page_cna'),
    path('apply/cna/save/', views.save_filled_pdf, name='save_filled_pdf_cna'),
    path('apply/cma/fill/', views.fill_pdf_cma, name='fill_pdf_cma'),
    path('apply/cma/render-page/', views.render_pdf_page_cma, name='render_pdf_page_cma'),
    path('apply/cma/save/', views.save_filled_pdf_cma, name='save_filled_pdf_cma'),
    path('apply/cna/download/', views.download_cna_pdf, name='download_cna_pdf'),
 
    path('apply/cma/', views.apply_cma, name='apply_cma'),
    path('apply/cma/download/', views.download_cma_pdf, name='download_cma_pdf'),
    #    path('admissions/', views.admissions, name='admissions'),
    path('admissions/tuition/', views.admissions_tuition, name='admissions_tuition'),
    path('admissions/financial-aid/', views.admissions_financial_aid, name='admissions_financial_aid'),
    path('admissions/requirements/', views.admissions_requirements, name='admissions_requirements'),
    path('admissions/faq/', views.admissions_faq, name='admissions_faq'),
    path('about/mission/', views.about_mission, name='about_mission'),
    path('about/team/', views.about_team, name='about_team'),
    path('about/accreditations/', views.about_accreditations, name='about_accreditations'),
    path('about/careers/', views.about_careers, name='about_careers'),
    path('apply/upload-document/', views.upload_application_document, name='upload_application_document'),
    path('apply/delete-document/<int:doc_id>/', views.delete_application_document, name='delete_application_document'),
]




    