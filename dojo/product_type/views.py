import logging

from django.contrib.admin.utils import NestedObjects
from django.db import DEFAULT_DB_ALIAS
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from dojo.filters import ProductTypeFilter
from dojo.forms import Product_TypeForm, Delete_Product_TypeForm, Add_Product_Type_MemberForm, \
    Edit_Product_Type_MemberForm, Delete_Product_Type_MemberForm, Add_Product_Type_GroupForm, \
    Edit_Product_Type_Group_Form, Delete_Product_Type_GroupForm
from dojo.models import Product_Type, Product_Type_Member, Role, Product_Type_Group, Test_Type
from dojo.utils import get_page_items, add_breadcrumb, is_title_in_breadcrumbs, get_object_or_none
from dojo.notifications.helper import create_notification
from django.db.models import Count, Q
from django.db.models.query import QuerySet
from django.conf import settings
from dojo.authorization.authorization import user_has_permission
from dojo.authorization.roles_permissions import Permissions
from dojo.authorization.authorization_decorators import user_is_authorized
from dojo.product_type.queries import get_authorized_product_types, get_authorized_members_for_product_type, \
    get_authorized_groups_for_product_type
from dojo.product.queries import get_authorized_products, get_authorized_dojo_meta


logger = logging.getLogger(__name__)

"""
Jay
Status: in prod
Product Type views
"""

def product_type(request):

    prod_types = get_authorized_product_types(Permissions.Product_Type_View)
    name_words = prod_types.values_list('name', flat=True)

    ptl = ProductTypeFilter(request.GET, queryset=prod_types)
    pts = get_page_items(request, ptl.qs, 25)

    
    pts.object_list = prefetch_for_product_type(pts.object_list)
    print("All test type details are filled")
    add_breadcrumb(title="Product Type List", top_level=True, request=request)
    return render(request, 'dojo/product_type.html', {
        'name': 'Product Type List',
        'pts': pts,
        'tools': settings.VISIBLE_TOOLS_NAME,
        'ptl': ptl,
        'name_words': name_words})



def prefetch_for_product_type(prod_types):
    prefetch_prod_types = prod_types
    
    if isinstance(prefetch_prod_types, QuerySet):  # old code can arrive here with prods being a list because the query was already executed
        active_findings_query = Q(prod_type__engagement__test__finding__active=True)
        prefetch_prod_types = prefetch_prod_types.prefetch_related('authorized_users')
        prefetch_prod_types = prefetch_prod_types.annotate(
            active_findings_count=Count('prod_type__engagement__test__finding__id', filter=active_findings_query))
        
        for key,value in settings.VISIBLE_TOOLS_NAME.items():
            tool_results = Q(prod_type__engagement__test__test_type__name=key,prod_type__engagement__test__finding__active=True)
            place_holder = {}
            place_holder = { value+"_findings_count": Count('prod_type__engagement__test__finding__id', filter=tool_results)}
            prefetch_prod_types = prefetch_prod_types.annotate(**place_holder)
        prefetch_prod_types = prefetch_prod_types.annotate(prod_count=Count('prod_type', distinct=True))
        
    else:
        print('unable to prefetch because query was already executed')
        logger.debug('unable to prefetch because query was already executed')

    return prefetch_prod_types



@user_passes_test(lambda u: u.is_staff)
def add_product_type(request):
    form = Product_TypeForm()
    if request.method == 'POST':
        form = Product_TypeForm(request.POST)
        if form.is_valid():
            product_type = form.save()
            if settings.FEATURE_AUTHORIZATION_V2:
                member = Product_Type_Member()
                member.user = request.user
                member.product_type = product_type
                member.role = Role.objects.get(is_owner=True)
                member.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 'Product type added successfully.',
                                 extra_tags='alert-success')
            create_notification(event='product_type_added', title=product_type.name,
                                product_type=product_type,
                                url=reverse('view_product_type', args=(product_type.id,)))
            return HttpResponseRedirect(reverse('product_type'))
    add_breadcrumb(title="Add Product Type", top_level=False, request=request)
    return render(request, 'dojo/new_product_type.html', {
        'name': 'Add Product Type',
        'form': form,
    })


@user_is_authorized(Product_Type, Permissions.Product_Type_View, 'ptid', 'view')
def view_product_type(request, ptid):
    pt = get_object_or_404(Product_Type, pk=ptid)
    members = get_authorized_members_for_product_type(pt, Permissions.Product_Type_View)
    groups = get_authorized_groups_for_product_type(pt, Permissions.Product_Type_View)
    products = get_authorized_products(Permissions.Product_View).filter(prod_type=pt)
    
    for key,value in settings.VISIBLE_TOOLS_NAME.items():
        tool_results = Q(engagement__test__test_type__name=key,engagement__test__finding__active=True)
        place_holder = {}
        place_holder = { value+"_findings_count": Count('engagement__test__finding__id', filter=tool_results)}
        products = products.annotate(**place_holder)
    
    add_breadcrumb(title="View Product Type", top_level=False, request=request)
    return render(request, 'dojo/view_product_type.html', {
        'name': 'View Product Type',
        'pt': pt,
        'tools': settings.VISIBLE_TOOLS_NAME,
        'products': products,
        'groups': groups,
        'members': members})


@user_is_authorized(Product_Type, Permissions.Product_Type_Delete, 'ptid', 'delete')
def delete_product_type(request, ptid):
    product_type = get_object_or_404(Product_Type, pk=ptid)
    form = Delete_Product_TypeForm(instance=product_type)

    if request.method == 'POST':
        if 'id' in request.POST and str(product_type.id) == request.POST['id']:
            form = Delete_Product_TypeForm(request.POST, instance=product_type)
            if form.is_valid():
                product_type.delete()
                messages.add_message(request,
                                     messages.SUCCESS,
                                     'Product Type and relationships removed.',
                                     extra_tags='alert-success')
                create_notification(event='other',
                                title='Deletion of %s' % product_type.name,
                                no_users=True,
                                description='The product type "%s" was deleted by %s' % (product_type.name, request.user),
                                url=request.build_absolute_uri(reverse('product_type')),
                                icon="exclamation-triangle")
                return HttpResponseRedirect(reverse('product_type'))

    collector = NestedObjects(using=DEFAULT_DB_ALIAS)
    collector.collect([product_type])
    rels = collector.nested()

    add_breadcrumb(title="Delete Product Type", top_level=False, request=request)
    return render(request, 'dojo/delete_product_type.html',
                  {'product_type': product_type,
                   'form': form,
                   'rels': rels,
                   })


@user_is_authorized(Product_Type, Permissions.Product_Type_Edit, 'ptid', 'staff')
def edit_product_type(request, ptid):
    pt = get_object_or_404(Product_Type, pk=ptid)
    authed_users = pt.authorized_users.all()
    members = get_authorized_members_for_product_type(pt, Permissions.Product_Type_Manage_Members)
    pt_form = Product_TypeForm(instance=pt, initial={'authorized_users': authed_users})
    if request.method == "POST" and request.POST.get('edit_product_type'):
        pt_form = Product_TypeForm(request.POST, instance=pt)
        if pt_form.is_valid():
            if not settings.FEATURE_AUTHORIZATION_V2:
                pt.authorized_users.set(pt_form.cleaned_data['authorized_users'])
            pt = pt_form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Product type updated successfully.',
                extra_tags="alert-success",
            )
            return HttpResponseRedirect(reverse("product_type"))
    add_breadcrumb(title="Edit Product Type", top_level=False, request=request)
    return render(request, 'dojo/edit_product_type.html', {
        'name': 'Edit Product Type',
        'pt_form': pt_form,
        'tools': settings.VISIBLE_TOOLS_NAME,
        'pt': pt,
        'members': members})


@user_is_authorized(Product_Type, Permissions.Product_Type_Manage_Members, 'ptid')
def add_product_type_member(request, ptid):
    pt = get_object_or_404(Product_Type, pk=ptid)
    memberform = Add_Product_Type_MemberForm(initial={'product_type': pt.id})
    if request.method == 'POST':
        memberform = Add_Product_Type_MemberForm(request.POST, initial={'product_type': pt.id})
        if memberform.is_valid():
            if memberform.cleaned_data['role'].is_owner and not user_has_permission(request.user, pt, Permissions.Product_Type_Member_Add_Owner):
                messages.add_message(request,
                                    messages.WARNING,
                                    'You are not permitted to add users as owners.',
                                    extra_tags='alert-warning')
            else:
                if 'users' in memberform.cleaned_data and len(memberform.cleaned_data['users']) > 0:
                    for user in memberform.cleaned_data['users']:
                        members = Product_Type_Member.objects.filter(product_type=pt, user=user)
                        if members.count() == 0:
                            product_type_member = Product_Type_Member()
                            product_type_member.product_type = pt
                            product_type_member.user = user
                            product_type_member.role = memberform.cleaned_data['role']
                            product_type_member.save()
                messages.add_message(request,
                                    messages.SUCCESS,
                                    'Product type members added successfully.',
                                    extra_tags='alert-success')
                return HttpResponseRedirect(reverse('view_product_type', args=(ptid, )))
    add_breadcrumb(title="Add Product Type Member", top_level=False, request=request)
    return render(request, 'dojo/new_product_type_member.html', {
        'pt': pt,
        'form': memberform,
    })


@user_is_authorized(Product_Type_Member, Permissions.Product_Type_Manage_Members, 'memberid')
def edit_product_type_member(request, memberid):
    member = get_object_or_404(Product_Type_Member, pk=memberid)
    memberform = Edit_Product_Type_MemberForm(instance=member)
    if request.method == 'POST':
        memberform = Edit_Product_Type_MemberForm(request.POST, instance=member)
        if memberform.is_valid():
            if not member.role.is_owner:
                owners = Product_Type_Member.objects.filter(product_type=member.product_type, role__is_owner=True).exclude(id=member.id).count()
                if owners < 1:
                    messages.add_message(request,
                                        messages.SUCCESS,
                                        'There must be at least one owner for Product Type {}.'.format(member.product_type.name),
                                        extra_tags='alert-warning')
                    if is_title_in_breadcrumbs('View User'):
                        return HttpResponseRedirect(reverse('view_user', args=(member.user.id, )))
                    else:
                        return HttpResponseRedirect(reverse('view_product_type', args=(member.product_type.id, )))
            if member.role.is_owner and not user_has_permission(request.user, member.product_type, Permissions.Product_Type_Member_Add_Owner):
                messages.add_message(request,
                                    messages.WARNING,
                                    'You are not permitted to make users to owners.',
                                    extra_tags='alert-warning')
            else:
                memberform.save()
                messages.add_message(request,
                                    messages.SUCCESS,
                                    'Product type member updated successfully.',
                                    extra_tags='alert-success')
                if is_title_in_breadcrumbs('View User'):
                    return HttpResponseRedirect(reverse('view_user', args=(member.user.id, )))
                else:
                    return HttpResponseRedirect(reverse('view_product_type', args=(member.product_type.id, )))
    add_breadcrumb(title="Edit Product Type Member", top_level=False, request=request)
    return render(request, 'dojo/edit_product_type_member.html', {
        'memberid': memberid,
        'form': memberform,
    })


@user_is_authorized(Product_Type_Member, Permissions.Product_Type_Member_Delete, 'memberid')
def delete_product_type_member(request, memberid):
    member = get_object_or_404(Product_Type_Member, pk=memberid)
    memberform = Delete_Product_Type_MemberForm(instance=member)
    if request.method == 'POST':
        memberform = Delete_Product_Type_MemberForm(request.POST, instance=member)
        member = memberform.instance
        if member.role.is_owner:
            owners = Product_Type_Member.objects.filter(product_type=member.product_type, role__is_owner=True).count()
            if owners <= 1:
                messages.add_message(request,
                                    messages.SUCCESS,
                                    'There must be at least one owner.',
                                    extra_tags='alert-warning')
                return HttpResponseRedirect(reverse('view_product_type', args=(member.product_type.id, )))

        user = member.user
        member.delete()
        messages.add_message(request,
                            messages.SUCCESS,
                            'Product type member deleted successfully.',
                            extra_tags='alert-success')
        if is_title_in_breadcrumbs('View User'):
            return HttpResponseRedirect(reverse('view_user', args=(member.user.id, )))
        else:
            if user == request.user:
                return HttpResponseRedirect(reverse('product_type'))
            else:
                return HttpResponseRedirect(reverse('view_product_type', args=(member.product_type.id, )))
    add_breadcrumb(title="Delete Product Type Member", top_level=False, request=request)
    return render(request, 'dojo/delete_product_type_member.html', {
        'memberid': memberid,
        'form': memberform,
    })


@user_is_authorized(Product_Type, Permissions.Product_Type_Group_Add, 'ptid')
def add_product_type_group(request, ptid):
    pt = get_object_or_404(Product_Type, pk=ptid)
    group_form = Add_Product_Type_GroupForm(initial={'product_type': pt.id})

    if request.method == 'POST':
        group_form = Add_Product_Type_GroupForm(request.POST, initial={'product_type': pt.id})
        if group_form.is_valid():
            if group_form.cleaned_data['role'].is_owner and not user_has_permission(request.user, pt, Permissions.Product_Type_Group_Add_Owner):
                messages.add_message(request,
                                    messages.WARNING,
                                    'You are not permitted to add groups as owners.',
                                    extra_tags='alert-warning')
            else:
                if 'groups' in group_form.cleaned_data and len(group_form.cleaned_data['groups']) > 0:
                    for group in group_form.cleaned_data['groups']:
                        groups = Product_Type_Group.objects.filter(product_type=pt, group=group)
                        if groups.count() == 0:
                            product_type_group = Product_Type_Group()
                            product_type_group.product_type = pt
                            product_type_group.group = group
                            product_type_group.role = group_form.cleaned_data['role']
                            product_type_group.save()
                messages.add_message(request,
                                     messages.SUCCESS,
                                     'Product type groups added successfully.',
                                     extra_tags='alert-success')
                return HttpResponseRedirect(reverse('view_product_type', args=(ptid,)))

    add_breadcrumb(title="Add Product Type Group", top_level=False, request=request)
    return render(request, 'dojo/new_product_type_group.html', {
        'pt': pt,
        'form': group_form,
    })


@user_is_authorized(Product_Type_Group, Permissions.Product_Type_Group_Edit, 'groupid')
def edit_product_type_group(request, groupid):
    group = get_object_or_404(Product_Type_Group, pk=groupid)
    groupform = Edit_Product_Type_Group_Form(instance=group)

    if request.method == 'POST':
        groupform = Edit_Product_Type_Group_Form(request.POST, instance=group)
        if groupform.is_valid():
            if group.role.is_owner and not user_has_permission(request.user, group.product_type, Permissions.Product_Type_Group_Add_Owner):
                messages.add_message(request,
                                     messages.WARNING,
                                     'You are not permitted to make groups owners.',
                                     extra_tags='alert-warning')
            else:
                groupform.save()
                messages.add_message(request,
                                     messages.SUCCESS,
                                     'Product type group updated successfully.',
                                     extra_tags='alert-success')
                if is_title_in_breadcrumbs('View Group'):
                    return HttpResponseRedirect(reverse('view_group', args=(group.group.id,)))
                else:
                    return HttpResponseRedirect(reverse('view_product_type', args=(group.product_type.id,)))

    add_breadcrumb(title="Edit Product Type Group", top_level=False, request=request)
    return render(request, 'dojo/edit_product_type_group.html', {
        'groupid': groupid,
        'form': groupform
    })


@user_is_authorized(Product_Type_Group, Permissions.Product_Type_Group_Delete, 'groupid')
def delete_product_type_group(request, groupid):
    group = get_object_or_404(Product_Type_Group, pk=groupid)
    groupform = Delete_Product_Type_GroupForm(instance=group)

    if request.method == 'POST':
        groupform = Delete_Product_Type_GroupForm(request.POST, instance=group)
        group = groupform.instance
        group.delete()
        messages.add_message(request,
                             messages.SUCCESS,
                             'Product type group deleted successfully.',
                             extra_tags='alert-success')
        if is_title_in_breadcrumbs('View Group'):
            return HttpResponseRedirect(reverse('view_group', args=(group.group.id, )))
        else:
            # TODO: If user was in the group that was deleted and no longer has access, redirect them to the product
            #  types page
            return HttpResponseRedirect(reverse('view_product_type', args=(group.product_type.id, )))

    add_breadcrumb("Delete Product Type Group", top_level=False, request=request)
    return render(request, 'dojo/delete_product_type_group.html', {
        'groupid': groupid,
        'form': groupform
    })
