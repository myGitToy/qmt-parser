from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile, Item
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
#用于证券数据连接
from django.db import connection
from .forms import StockDataForm
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
from django.core.paginator import Paginator
from .models import StockData
# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

@login_required
def exchange_stamina_for_gold(request):
    profile = Profile.objects.get(user=request.user)
    if profile.stamina >= 10:
        profile.stamina -= 10
        profile.gold += 10
        profile.save()
    return redirect('watu:profile')



"""
def buy_item(request, item_id):
    profile = Profile.objects.get(user=request.user)
    item = Item.objects.get(id=item_id)
    if profile.gold >= item.price:
        profile.gold -= item.price
        profile.save()
        # 假设你有一个用户物品的模型来存储购买的物品
        # UserItem.objects.create(user=request.user, item=item)
    return redirect('watu:profile')
"""
@login_required
def buy_item(user, item_id):
    profile = get_object_or_404(Profile, user=user)
    item = get_object_or_404(Item, id=item_id)

    if profile.gold >= item.price:
        profile.gold -= item.price
        profile.inventory.add(item)
        profile.save()
        return JsonResponse({'status': 'success', 'message': 'Item purchased successfully.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Not enough gold.'})

@login_required
def purchase_view(request, item_id):
    if request.method == 'POST':
        success = buy_item(request.user, item_id)
        if success:
            return JsonResponse({'status': 'success', 'message': 'Item purchased successfully.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Not enough gold.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@login_required
def profile(request):
    profile = Profile.objects.get(user=request.user)
    inventory_items = profile.inventory.all()
    items = Item.objects.all()
    return render(request, 'watu/profile.html', {'profile': profile, 'items': items, 'inventory_items': inventory_items})

def stock_data_view(request):
    if request.method == 'POST':
        form = StockDataForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            ktype = form.cleaned_data['ktype']
            fqtype = form.cleaned_data['fqtype']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            query = f"""
                SELECT date, open, high, low, close, volume, money FROM tspro_{ktype}
                WHERE code = '{code}' AND date BETWEEN '{start_date}' AND '{end_date}'
            """
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

            # 将查询结果转换为DataFrame
            df = pd.DataFrame(rows, columns=[ 'date', 'open', 'high', 'low', 'close', 'volume', 'money'])

            # 将 DataFrame 转换为列表
            data_list = df.to_dict('records')

            # 使用 Paginator 进行分页
            paginator = Paginator(data_list, 20)  # 每页显示20条数据
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)  

            # 绘制K线图
            plt.figure(figsize=(10, 5))
            plt.plot(df['date'], df['close'], label='收盘价')
            plt.xlabel('日期')
            plt.ylabel('价格')
            plt.title(f'{code} K线图')
            plt.legend()

            # 将图表保存为图片
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            #return render(request, 'watu/stock_data.html', {'rows': rows})
            return render(request, 'stock_data.html', {'form': form, 'rows': rows, 'image_base64': image_base64})   #正常+美化的写法
            #return render(request, 'watu/stock_data.html', {'form': form, 'page_obj': page_obj})    #返回分页数据
    else:
        form = StockDataForm()

    return render(request, 'watu/stock_data.html', {'form': form})