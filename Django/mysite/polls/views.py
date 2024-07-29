"""
Django 中的视图的概念是「一类具有相同功能和模板的网页的集合」。比如，在一个博客应用中，你可能会创建如下几个视图：

博客首页——展示最近的几项内容。
内容“详情”页——详细展示某项内容。
以年为单位的归档页——展示选中的年份里各个月份创建的内容。
以月为单位的归档页——展示选中的月份里各天创建的内容。
以天为单位的归档页——展示选中天里创建的所有内容。
评论处理器——用于响应为一项内容添加评论的操作。
而在我们的投票应用中，我们需要下列几个视图：

问题索引页——展示最近的几个投票问题。
问题详情页——展示某个投票的问题和不带结果的选项列表。
问题结果页——展示某个投票的结果。
投票处理器——用于响应用户为某个问题的特定选项投票的操作。
在 Django 中，网页和其他内容都是从视图派生而来。每一个视图表现为一个 Python 函数（或者说方法，如果是在基于类的视图里的话）。Django 将会根据用户请求的 URL 来选择使用哪个视图（更准确的说，是根据 URL 中域名之后的部分）。

在你上网的过程中，很可能看见过像这样美丽的 URL：ME2/Sites/dirmod.htm?sid=&type=gen&mod=Core+Pages&gid=A6CD4967199A42D9B65B1B。别担心，Django 里的 URL 样式 要比这优雅的多！

URL 样式是 URL 的一般形式 - 例如：/newsarchive/<year>/<month>/。

为了将 URL 和视图关联起来，Django 使用了 'URLconfs' 来配置。URLconf 将 URL 模式映射到视图。

本教程只会介绍 URLconf 的基础内容，你可以看看 URL调度器 以获取更多内容。
"""
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect,Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
# Create your views here.
from django.utils import timezone
from .models import Choice, Question
from django.template import loader

def index(request):
    latest_question_list = Question.objects.order_by("-pub_date")[:5]
    context = {"latest_question_list": latest_question_list}
    return render(request, "polls/index.html", context)

"""
继续增加功能
"""
def detail(request, question_id):
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, "polls/detail.html", {"question": question})

def results(request, question_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % question_id)

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))