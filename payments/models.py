from django.db import models
from django_bitcoin.currency import *
from decimal import Decimal
import datetime
import urllib

# Create your models here.

BITCOIN_CONFIRMATIONS_REQUIRED = getattr(
    settings, 
    "BITCOIN_CONFIRMATIONS_REQUIRED", 
    0)


def bitcoin_address_received(bitcoin_address, confirmations=BITCOIN_CONFIRMATIONS_REQUIRED):
    url = "http://blockchain.info/q/addressbalance/" + bitcoin_address + "?confirmations=" + str(confirmations)
    f = urllib.urlopen(url, None)
    data = f.read()
    r = Decimal(data) * Decimal("0.00000001")
    return r


class Merchant(models.Model):
    created_at = models.DateTimeField(default=datetime.datetime.now)
    updated_at = models.DateTimeField(auto_now=True)

    master_public_key = models.CharField(max_length=255, unique=True)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default='USD')
    uuid = models.CharField(max_length=50)


class Payment(models.Model):
    created_at = models.DateTimeField(default=datetime.datetime.now)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, default=None)

    bitcoin_address = models.CharField(max_length=50)
    btc_amount = models.DecimalField(max_digits=16, decimal_places=8)

    currency_amount = models.DecimalField(max_digits=16, decimal_places=2)

    merchant = models.ForeignKey(Merchant)

    received_least = models.DecimalField(max_digits=16, decimal_places=8, default=Decimal(0))

    def exchange_rate(self):
        return Decimal(self.currency_amount / self.btc_amount).quantize(Decimal("0.01"))
    
    # Return raw Bitcoin address
    def __unicode__(self):
        return "bitcoin:"+self.bitcoin_address+"&amount="+str(self.btc_amount)
    
    def received(self):
        r = bitcoin_address_received(self.bitcoin_address)
        if r > self.received_least:
            self.received_least = r
            self.save()
        return r

    def is_paid(self):
        if self.received_least >= self.btc_amount:
            return True
        if self.received() >= self.btc_amount:
            return True
        return False



