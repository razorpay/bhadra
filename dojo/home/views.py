from collections import defaultdict
from datetime import timedelta
from typing import Dict

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render
from django.utils import timezone
from dojo.filters import ProductTypeFilter

from django.db.models import Count, Q
from dojo.utils import add_breadcrumb, get_punchcard_data ,get_page_items
from dojo.models import Answered_Survey
from dojo.authorization.roles_permissions import Permissions
from dojo.engagement.queries import get_authorized_engagements
from dojo.finding.queries import get_authorized_findings
from dojo.product_type.queries import get_authorized_product_types
from dojo.product.queries import get_authorized_products
from dojo.product_type.views import prefetch_for_product_type


def home(request: HttpRequest) -> HttpResponse:
    return HttpResponseRedirect(reverse('dashboard'))

def product_type_info(request):

    prod_types = get_authorized_product_types(Permissions.Product_Type_View)
    name_words = prod_types.values_list('name', flat=True)

    ptl = ProductTypeFilter(request.GET, queryset=prod_types)
    pts = get_page_items(request, ptl.qs, 25)

   
    pts.object_list = prefetch_for_product_type(pts.object_list)
    add_breadcrumb(title="Product Type List", top_level=True, request=request)
    return {
        'name': 'Product Type List',
        'pts': pts,
        'tools': settings.VISIBLE_TOOLS_NAME,
        'ptl': ptl,
        'name_words': name_words}

def dashboard(request: HttpRequest) -> HttpResponse:
    engagements = get_authorized_engagements(Permissions.Engagement_View).distinct()
    findings = get_authorized_findings(Permissions.Finding_View).distinct()

    findings = findings.filter(duplicate=False)

    engagement_count = engagements.filter(active=True).count()

    today = timezone.now().date()

    date_range = [today - timedelta(days=6), today]  # 7 days (6 days plus today)
    finding_count = findings\
        .filter(created__date__range=date_range)\
        .count()
    mitigated_count = findings\
        .filter(mitigated__date__range=date_range)\
        .count()
    accepted_count = findings\
        .filter(risk_acceptance__created__date__range=date_range)\
        .count()

    severity_count_all = get_severities_all(findings)
    severity_count_by_month = get_severities_by_month(findings, today)
    punchcard, ticks = get_punchcard_data(findings, today - relativedelta(weeks=26), 26)

    if request.user.is_staff:
        unassigned_surveys = Answered_Survey.objects.filter(assignee_id__isnull=True, completed__gt=0, ) \
            .filter(Q(engagement__isnull=True) | Q(engagement__in=engagements))
    else:
        unassigned_surveys = None

    if request.user.is_superuser and not settings.FEATURE_AUTHORIZATION_V2:
        message = '''Legacy authorization will be removed with version 2.5.0 / end of November 2021.
                     If you have set `FEATURE_AUTHORIZATION_V2` to `False` in your local
                     configuration, remove this local setting and start using
                     the new authorization.'''
        messages.add_message(request, messages.WARNING, message, extra_tags='alert-warning')
    product_list=product_type_info(request)

    add_breadcrumb(request=request, clear=True)
    return render(request, 'dojo/dashboard.html', {
        **product_list,
        'engagement_count': engagement_count,
        'finding_count': finding_count,
        'mitigated_count': mitigated_count,
        'accepted_count': accepted_count,
        'critical': severity_count_all['Critical'],
        'high': severity_count_all['High'],
        'medium': severity_count_all['Medium'],
        'low': severity_count_all['Low'],
        'info': severity_count_all['Info'],
        'by_month': severity_count_by_month,
        'punchcard': punchcard,
        'ticks': ticks,
        'surveys': unassigned_surveys,
    })


def get_severities_all(findings) -> Dict[str, int]:
    severities_all = findings.values('severity').annotate(count=Count('severity')).order_by()
    return defaultdict(lambda: 0, {s['severity']: s['count'] for s in severities_all})


def get_severities_by_month(findings, today):
    severities_by_month = findings\
        .filter(created__date__gte=(today - relativedelta(months=6)))\
        .values('created__year', 'created__month', 'severity')\
        .annotate(count=Count('severity'))\
        .order_by()

    # The chart expects a, b, c, d, e instead of Critical, High, ...
    SEVERITY_MAP = {
        'Critical': 'a',
        'High':     'b',  # noqa: E241
        'Medium':   'c',  # noqa: E241
        'Low':      'd',  # noqa: E241
        'Info':     'e',  # noqa: E241
    }

    results = {}
    for ms in severities_by_month:
        key = f"{ms['created__year']}-{ms['created__month']:02}"
        month_stats = results.setdefault(key, {'y': key, 'a': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, None: 0})
        month_stats[SEVERITY_MAP.get(ms['severity'])] += ms['count']

    return [v for k, v in sorted(results.items())]
