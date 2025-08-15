# forms.py
from django import forms

class StockDataForm(forms.Form):
    code = forms.CharField(label='证券代码', max_length=10)
    ktype = forms.ChoiceField(label='K线类型', choices=[('1d', '日线'), ('1w', '周线'), ('1m', '月线')])
    fqtype = forms.ChoiceField(label='复权类型', choices=[('qfq', '前复权'), ('hfq', '后复权')])
    start_date = forms.DateField(label='开始日期', widget=forms.SelectDateWidget)
    end_date = forms.DateField(label='结束日期', widget=forms.SelectDateWidget)