from django import template
register = template.Library()

@register.filter
def get_attribute(obj, name):

    if hasattr(obj, name):
        return getattr(obj, name)
    else:
        return ''
    
@register.filter
def get_attribute_count(obj, name):
    name += "_findings_count"
    if hasattr(obj, name):
        return getattr(obj, name)
    else:
        return ''
    
@register.filter
def to_and(value):
    return value.replace(" ","_")

@register.filter
def make_capitalize(value):
    value = value.replace("_"," ").replace("-", " ")
    return value.capitalize()