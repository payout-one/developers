# Apple Pay JS Integration

#### Prerequisites

Before you start, you need to:

  * Add a payment method to your browser. For example, you can save a card in Chrome, add a card to your Google Pay account or add a card to your Wallet for Safari.
  * Serve your application over HTTPS. This is a requirement both in development and in production. One way to get up and running is to use a service like ngrok.
  * Send us domains from which Apple Pay will be served for verification purposes, both for development and production.

**Verify your domain with Apple Pay**
To use Apple Pay, you need to register with Apple all of your web domains that will show an Apple Pay button. This includes both top-level domains (for example, payout.one) and subdomains (for example, shop.payout.one). You need to do this for domains you use in both production and testing. When testing locally, use a tool like ngrok to get an HTTPS domain.

Important note: Apple’s documentation for Apple Pay on the Web describes their process of “merchant validation”, which Payout handles for you behind the scenes. You don’t need to create an Apple Merchant ID, CSR, and so on, as described in their documentation, and should instead just follow these steps:

1. Tell Payout to register your domain with Apple and provide you with domain association file.
2. Download provided domain association file and host it at /.well-known/apple-developer-merchantid-domain-association on your site. For example, if you’re registering https://example.com, make that file available at https://example.com/.well-known/apple-developer-merchantid-domain-association.
3. After registering your domains, you can make payments on your site using your publishable API keys.

#### 1. Set up HTML+JS

Include JS library and prepare container in which payment button will be rendered.

```html
  <script src="https://js.payout.one.com/v1/"></script>
  <div id="payment-request-button">
    <!-- Apple Pay button will be inserted here. -->
  </div>
```

Prepare data and initialize Payout library with environment you want to use (TEST, PROD) and your's publishable API key which you can find in yours account at [app.payout.one](app.payout.one) in API Keys section.

```javascript
  const env = 'TEST'; // environment selection
  const api_key = 'xYdDRpvMQNkjOXKVdA3bnW8gB5ZPEeaV' // public API key

  var payout = new Payout(env, api_key);
```

#### 2. Create Checkout
Next step is to create checkout from your server in order to obtain token used for payment completion.

Please refer to [Simple Payment](https://developers.payout.tech/#/use-cases/simple-payment) page for details, or specific implementation of our API via library (e.g. payout-php) or supported eshop platforms like WooComerce etc., listed on [Integrations](https://developers.payout.tech/#/integrations) page.

Returned checkout contains `token` attribute used for completing the ongoing payment flow.

#### 3. Create Apple Pay button
Before rendering Apple Pay button it's required to check if Apple Pay is available and if it's payment button can be rendered, like in the example below with some sample data:

```javascript
  const data = {
      amount: "4",
      currency: "EUR",
      country: "SK",
      merchant: "Merchant name"
    }

  payout.applePay.canMakePayments().then(function (result) {
    // payment button can be rendered
    if (result) {
      payout.applePay.createButton('#payment-request-button', data);
    }
  }).catch(function (e) {
    // handle rejected Promise
    console.log(e);
  });
```

Sample CSS style for Apple Pay button:

```css
  #payment-request-button button.apple-pay {
    -webkit-appearance: -apple-pay-button;
    -apple-pay-button-type: buy;
    -apple-pay-button-style: black;
    cursor: pointer;
  }
```

#### 4. Complete payment
Next listen to the `completePayment` event and confirm payment with checkout token from the second step.

```javascript
  payout.applePay.on('completePayment', data => payout.confirmPayment(token).then(function (confirmResult) {
    if (confirmResult.error) {
      // completion error
    } else {
      // completion success
    }
  }));
```

#### Test your integration
To test your integration you must use HTTPS and a supported browser.

In addition, each payment method and browser has specific requirements:

**Safari**
  * Safari on Mac running macOS Sierra or later
  * An iPhone (not an iPad; Safari doesn’t support them yet) with a card in its Wallet paired to your Mac with Handoff, or a Mac with TouchID. Instructions can be found on Apple’s Support site.
  * Make sure you’ve verified your domain with Apple Pay.

**Mobile Safari**
  * Mobile Safari on iOS 10.1 or later
  * A card in your Wallet (go to Settings → Wallet & Apple Pay)
  * Make sure you’ve verified your domain with Apple Pay.

For additional details and testing cards please refer to official Apple documentation [here](https://developer.apple.com/apple-pay/sandbox-testing/).
