# Family portal payments with Razorpay (test mode)

The Care Plan (`CARE_MONTHLY`) can be paid through **Razorpay Orders + Checkout**. It is one payment per 30 days of optional portal
features. It never grants access to a resident and never affects emergency alerts. The default is still the simulated sandbox.

## How a payment flows
1. The family member presses **Pay ... with Razorpay**. The server creates an order for the plan price and returns the order id and the
   **public** key id.
2. Razorpay's own checkout window opens. Card, UPI and bank details are typed there and never reach this server.
3. When it finishes, the browser sends only `order_id`, `payment_id` and `signature` to `POST /payments/razorpay/verify`.
4. The server (a) checks the signature (HMAC-SHA256 with the key secret over `order_id|payment_id`), (b) asks Razorpay for the payment,
   (c) requires the same order, the plan amount and currency and a captured status (an *authorized* payment is captured first), and only then
   (d) activates the subscription through the shared event processor: replay protection, amount check, and an administrator's hold is never
   lifted by a payment.
5. Backup path: Razorpay's signed webhook (`payment.captured`, `payment.failed`) at `POST /payments/webhooks/razorpay` ends in the same
   processor and the same event ids, so a payment confirmed both ways counts once.

## Setup (you do this, secrets stay with you)
1. Razorpay dashboard in **Test mode**: *Account & Settings > API Keys > Generate Test Key*. You get a key id (`rzp_test_...`, public) and a
   key secret (shown once). **Never paste the secret into chat, an issue or the repository.**
2. Render service > **Environment**: set `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, then `PAYMENTS_MODE=razorpay`. (With `PAYMENTS_MODE=razorpay`
   and no keys the app refuses to start, on purpose.)
3. Optional webhook: Razorpay dashboard > *Webhooks > Add*: URL `https://<your-api>/payments/webhooks/razorpay`, events `payment.captured` and
   `payment.failed`, and a secret of your choice, which you set as `RAZORPAY_WEBHOOK_SECRET`.
4. In the family portal the panel shows **RAZORPAY TEST MODE - no real money**. In the payment window use the test card
   `4111 1111 1111 1111`, any future expiry and any 3-digit CVV, or the UPI id `success@razorpay`.

## Safety rules built in
- Secrets come only from the environment, are never logged, returned or put in an error message.
- A **live** key (`rzp_live_...`) is refused at start-up unless `RAZORPAY_ALLOW_LIVE=1` is set deliberately.
- Nothing the browser says is trusted: signature, then a fetch from Razorpay, then order/amount/currency/status checks.
- Another user's order cannot be confirmed (404), and a wrong amount is recorded and rejected.
- `RAZORPAY_API_BASE` (used by the tests to point at a fake Razorpay) cannot be changed in production.

## Not included
Automatic monthly renewal (Razorpay Subscriptions needs its own plan set-up and account approval). Each period is paid by the family member
again; if it is missed the existing grace period and expiry rules apply. Refunds are made in the Razorpay dashboard.
