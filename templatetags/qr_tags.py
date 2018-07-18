from django import template

register = template.Library()


@register.inclusion_tag('qr_tag.html', takes_context=True)
def qr_from_text(context, text, size='M'):
    if type(size) == type(0) or type(size) == type('') and size.isdigit():
        # this checks if it's an integer or a string with an integer
        actual_size = size
    else:
        sizes_dict = {'s': 120, 'm': 230, 'l': 350}
        if not size.lower() in sizes_dict:
            size = 'm'
        actual_size = sizes_dict[size.lower()]
    return {'text': text, 'size': actual_size}