from django.urls import path
from .views import (
    CreatePaymentView,
    VerifyPaymentView,
    PaymentStatusView
)

urlpatterns = [
    path("create/", CreatePaymentView.as_view()),
    path("verify/", VerifyPaymentView.as_view()),
    path("status/<str:token>/", PaymentStatusView.as_view()),
]
