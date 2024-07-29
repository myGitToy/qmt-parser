from django.db import models
from django.contrib.auth.models import User
class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stamina = models.IntegerField(default=100)
    gold = models.IntegerField(default=0)
    inventory = models.ManyToManyField(Item, blank=True)
    def use_item(self, item):
        if item.name == '苹果':
            self.stamina += 10
            self.save()
            item.delete()  # 假设使用后物品被删除
    def __str__(self):
        return self.user.username
    
class StockData(models.Model):
    """
    股票数据model
    """
    #code = models.CharField(max_length=10)
    date = models.DateField()
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.IntegerField()
    money = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = 'tspro_1d'

    def __str__(self):
        return f"{self.date} - {self.close}"
