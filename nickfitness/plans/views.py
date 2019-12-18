from django.shortcuts import render, get_object_or_404, redirect
from .forms import CustomSignupForm
from django.urls import reverse_lazy
from django.views import generic
from .models import FitnessPlan, Customer
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
import stripe
stripe.api_key = 'sk_test_nuWJOw3lDoNZiEuwZONJlMwJ00eFdh2VCg'

def home(request):
    plans = FitnessPlan.objects
    return render(request, 'plans/home.html', {'plans':plans})

def plan(request,pk):
    plan = get_object_or_404(FitnessPlan, pk=pk)
    if plan.premium:
        return redirect('join')
    else:
        return render(request, 'plans/plan.html', {'plan': plan})

def join(request):
    return render(request, 'plans/join.html')

@login_required
def checkout(request):

    coupons = {'halloween': 31, 'welcome': 10}

    if request.method == 'POST':
        ## Process payments
        stripe_customer = stripe.Customer.create(
            email=request.user.email, source=request.POST['stripeToken'])
        plan = 'plan_GMXQDbt0nCfkJ5'  # Add plan id for month
        if request.POST['plan'] == 'yearly':
            plan = 'plan_GMXRkAo9z5JJs3'
        if request.POST['coupon'] in coupons:
            percentage = coupons[request.POST['coupon'].lower()]
            try:
                coupon = stripe.Coupon.create(duration='once', id=request.POST['coupon'].lower(),
                                              percent_off=percentage)
            except:
                pass
            subscription = stripe.Subscription.create(customer=stripe_customer.id,
                                                      items=[{'plan': plan}], coupon=request.POST['coupon'].lower())
        else:
            subscription = stripe.Subscription.create(customer=stripe_customer.id,
                                                      items=[{'plan': plan}])

        customer = Customer()
        customer.user = request.user
        customer.stripeid = stripe_customer.id
        customer.membership = True
        customer.cancel_at_period_end = False
        customer.stripe_subscription_id = subscription.id
        customer.save()

        return redirect('home')
    else:
        coupon = 'none'
        plan = 'monthly'
        price = 1000
        og_dollar = 10
        coupon_dollar = 0
        final_dollar = 10
        if request.method == 'GET' and 'plan' in request.GET:
            if request.GET['plan'] == 'yearly':
                plan = 'yearly'
                price = 10000
                og_dollar = 100
                final_dollar = 100
        if request.method == 'GET' and 'coupon' in request.GET:
            if request.GET['coupon'].lower() in coupons:
                coupon = request.GET['coupon'].lower()
                percentage = coupons[request.GET['coupon'].lower()]
                coupon_price = int((percentage / 100) * price)
                price = price - coupon_price
                coupon_dollar = str(coupon_price)[
                    :-2] + '.' + str(coupon_price)[-2:]
                final_dollar = str(price)[:-2] + '.' + str(price)[-2:]
                
        return render(request, 'plans/checkout.html',
        {'plan':plan,'coupon':coupon,'price':price,'og_dollar':og_dollar,
        'coupon_dollar':coupon_dollar,'final_dollar':final_dollar})

def settings(request):
    return render(request, 'registration/settings.html')

class SignUp(generic.CreateView):
    form_class = CustomSignupForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        valid = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        new_user = authenticate(username=username, password=password)
        login(self.request, new_user)
        return valid
