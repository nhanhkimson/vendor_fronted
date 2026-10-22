# Setup and a ten-minute demo

Setup commands, credentials, and the network URLs are in the repository [README](../README.md). `./dev.sh` prints the current LAN address. Swagger is `/api/docs` on the web port, with Authorize using the email and the password `demo`.

## Demo

1. Open `/login` and choose Maya. The password on the card is `demo`.
2. Add a product from AnnesCraftworks and one from another shop. Pay on `/checkout` with `4242 4242 4242 4242`.
3. Open the order. There is one parent and one sub-order per shop. Only the shipped shop has a tracking number after Jess ships.
4. Sign in as Jess. `/seller/orders` lists her shop only. Ship `O-1001-V06` with a tracking number.
5. Sign in as Kein and open Jess's sub-order. The API returns 404.
6. Sign in as Ava. On `/admin/commissions`, revise the growth rule. Commission lines already stored keep the old rate. Ending the platform rule returns 409 `platform_rule`.
7. As Jess, request `PAY-06`. As Daniel, sign it. Daniel's second signature is 409 `already_signed`. Jess cannot sign. Lin signs, and Daniel pays with a reference such as `TRF-1008`. The trial balance stays balanced.
8. As Lin, flag a review. The stars do not change when Jess replies.
9. As Ava, open `/admin/reports` and download the CSV. Jess's export contains only V06.

Reset the demo data with `cd backend && uv run python -m app.seed` if a walk-through should start from the seed again.
