from django.urls import path
from . import views

app_name = 'watu'
urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('exchange/', views.exchange_stamina_for_gold, name='exchange'),
    path('buy/<int:item_id>/', views.buy_item, name='buy_item'),
    path('stock_data/', views.stock_data_view, name='stock_data'),
]