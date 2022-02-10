from django import template
from notifications.models import Notification

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(is_safe=True)
def sumfields(value):
    total = value.total
    concluido = value.concluido
    sum = total + concluido
    return sum

@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()

@register.filter(name='get_field2')
def get_field2(obj,field_name):
    return obj._meta.get_fields()