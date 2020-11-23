import sys
from io import BytesIO

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.urls import reverse

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class MinResolutionErrorExceptions(Exception):
    pass


class CategoryManager(models.Manager):
    CATEGORY_NAME_COUNT_NAME = {
        'Кактусы': 'cactusproduct__count',
        'Суккуленты': 'succulentproduct__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count('cactusproduct', 'succulentproduct')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (700, 700)
    MAX_IMAGE_SIZE = 3145728

    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Фотография')
    description = models.TextField(verbose_name='Описание', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        image = self.image
        img = Image.open(image)
        min_height, min_width = Product.MIN_RESOLUTION
        if img.height < min_height or img.width < min_width:
            raise MinResolutionErrorExceptions('Разрешение изображения меньше минимального! ')
        image = self.image
        img = Image.open(image)
        new_img = img.convert('RGB')
        resized_new_img = new_img.resize((800, 800), Image.ANTIALIAS)
        filestream = BytesIO()
        resized_new_img.save(filestream, 'PNG', quality=90)
        filestream.seek(0)
        name = '{}.{}'.format(*self.image.name.split('.'))
        self.image = InMemoryUploadedFile(
            filestream, 'ImageField', name, 'png/image', sys.getsizeof(filestream), None
        )
        super().save(*args, **kwargs)


class CactusProduct(Product):
    needles = models.CharField(max_length=255, verbose_name='Иголки')
    flower = models.CharField(max_length=255, verbose_name='Цветок')
    height = models.CharField(max_length=255, verbose_name='Высота')
    frequency_of_watering = models.CharField(max_length=255, verbose_name='Переодичность полива')
    flower_pot_diameter = models.CharField(max_length=255, verbose_name='Диаметр цветочного горшка')

    def __str__(self):
        return "{}: {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class SucculentProduct(Product):
    height = models.CharField(max_length=255, verbose_name='Высота')
    flower = models.CharField(max_length=255, verbose_name='Цветок')
    frequency_of_watering = models.CharField(max_length=255, verbose_name='Переодичность полива')
    flower_pot_diameter = models.CharField(max_length=255, verbose_name='Диаметр цветочного горшка')

    def __str__(self):
        return "{}: {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class CartProduct(models.Model):
    user = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')

    def __str__(self):
        return "Продукт: {} (для корзины)".format(self.content_object.title)


class Cart(models.Model):
    owner = models.ForeignKey('Customer', verbose_name='Владелец', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона')
    address = models.CharField(max_length=255, verbose_name='Адрес')

    def __str__(self):
        return "Покупатель: {} {}".format(self.user.first_name, self.user.last_name)


class LatestProductManager:
    CT_MODEL_MODEL_CLASS = {
        'Cactus': CactusProduct,
        'Succulent': SucculentProduct
    }

    # Добавить несколько входящих аргументов

    @staticmethod
    def get_products_for_main_page(self, *args, **kwargs):
        ct_model = ContentType.objects.get_for_model(self)
        last_product_list = list(ct_model.model_class()._base_manager.all().order_by('-id')[:5])
        return last_product_list


class LatestProducts:
    objects = LatestProductManager()
