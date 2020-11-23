from django.forms import ModelChoiceField, ModelForm, ValidationError
from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import *


class CactusAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].help_text = mark_safe(
            """<span style="color:red; font-size: 13px;">При загрузке изображения с разрешением больше {}x{} оно будет 
            обрезано</span>""".format(*Product.MAX_RESOLUTION))

    def clean_image(self):
        image = self.cleaned_data['image']
        img = Image.open(image)
        min_height, min_width = Product.MIN_RESOLUTION
        if image.size > Product.MAX_IMAGE_SIZE:
            raise ValidationError('Размер изображение не должен превышать 3 Мб! ')
        if img.height < min_height or img.width < min_width:
            raise ValidationError('Разрешение изображения меньше минимального! ')
        return image


class CactusAdmin(admin.ModelAdmin):
    form = CactusAdminForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='cactus'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SucculentAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            return ModelChoiceField(Category.objects.filter(slug='succulent'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Category)
admin.site.register(CactusProduct, CactusAdmin)
admin.site.register(SucculentProduct, SucculentAdmin)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
