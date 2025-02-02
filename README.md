# DataView [![data-view](https://github.com/OrionExplorer/data-view/actions/workflows/data-view-django.yml/badge.svg)](https://github.com/OrionExplorer/data-view/actions/workflows/data-view-django.yml)
DataView - API for all the data you need.

## Stack
### Django 5.1.5
[Custom docker image](https://github.com/OrionExplorer/data-view/blob/main/data-view.dockerfile) named `core` is based on Debian 12 "bookworm". Runs on Gunicorn on port `8888` by default.

### PostgreSQL 17.2
Named `db`. Runs on port `5455` by default.

### Nginx
Named `nginx`. Runs as reverse proxy for Django (upstream port `8888`) and listens on port `9393` by default.

### Docker & docker compose
For faster and safer deployments.

## Requests
### /items/
`https://data-view.local:9393/items/`

To gather information on available models and their configuration.

### /items/\<str:model\>/
`https://data-view.local:9393/items/shop/?start=0&limit=25`

To get data from specific model.
##### Parameters
* start (if not provided, parameter is set to 0)
* limit (if not provided, parameter is set to 25)
* every field from model as filter (combination of multiple fields is possible)

Each request details are saved in `/var/log/data-view/api.log`. If `/var/log/` is unaccesible, `log` folder is created in app main path as a fallback.

## Usage
### API key
Main model is `ApiKey` linked with `User`. It has auto-generated `api_key` to use with every request in custom `x-api-key` header.
It also contains `credits` - a currency to spend on data transfers. Each queryable model has to have a `billing` property, for example:
```python
billing = {
    'chunk_KB': 10,
    'credits': 0.1,
    'min_chunk_KB': 10
}
```
* `chunk_KB` - for how much KB of transferred data we charge `credits`
* `credits` - how much credits we charge for `chunk_KB` of transferred data
* `min_chunk_KB` - minimum chunk size we charge `credits` for

#### Example
Let's say the request we performed generated 651 records in response, and it's size is 248.3 KB.
We charge 0.1 credit per 10 KB of data.
Our request generated 25 chunks (248.3 KB / 10 KB).
Credits charged for our request: 2.5 (25 of 10 KB chunks x 0.1 credit).

Credits to charge are calculated prior to sending the response. If the request exceeds available credits, error is returned.

### Billing
Each request is saved with `ApiKeyCreditHistory` model. It contains following details:
* API key used for the request
* Date and time of the request
* Requested endpoint with query parameters
* Response size (in KB)
* Request chunk size (in KB) from model's `billing` property at the time of action
* Number of generated chunks of data
* Credit cost per chunk from model's `billing` property at the time of action
* Total credit cost of the request
* Credit balance before charge
* IP address
* Unique request identificator as stored in log the file

### Top-up
To top-up `credits` in `ApiKey`, an `ApiKeyCreditTopUp` model is used. It contains following information:
* API key
* Number of credits to add to `ApiKey`'s `credits` value
* Date and time

## Feeding data
Each dataset is spearate Django Application:
```bash
root@localhost:~/data-view# python manage.py startapp ShopsAPI
```
You only have to create your models (with the definition of billing). And, of course, feed them with data. The rest - that is, making them available through the API - is handled by the system. [See the example here](https://github.com/OrionExplorer/data-view/blob/main/data-view/ShopsAPI/models.py).

## TODO
* [x] New model `ApiKey`:
  * [x] api_key (`CharField`)
  * [x] credits (~~`BigAutoField`~~ `DecimalField`)
  * [x] user (foreign key to `User` model)
  * [x] created (`DateTimeField`)
* [x] Views decorators:
  * [x] `@valid_api_key` checking for `X-API-KEY` in request header
* [x] New model `ApiKeyCreditHistory`
  * [x] api_key (`ForeignKey`)
  * [x] data_request_uri (`CharField`)
  * [x] response_size (`IntegerField`)
  * [x] request_chunk_size (`IntegeField`)
  * [x] chunk_count (`IntegerField`)
  * [x] credit_per_chunk (`DecimalField`)
  * [x] total_credit_cost (`DecimalFied`)
  * [x] credit_balance (`DecimalFild`)
  * [x] timestamp (`DateTimeField`)
  * [x] ip (`GenericIPAddressField`)
* [x] `BillingMixin` to define billing information for each set of data (model):
  * [x] `chunk_KB`
  * [x] `credits`
  * [x] `min_chunk_KB`
* [x] New model `ApiKeyCreditTopUp`:
  * [x] api_key (`ForeignKey`)
  * [x] credit_top_up (`DecimalField`)
  * [x] timestamp (`DateTimeField`)
* [x] Universal field filtering capability for any model
* [x] New endpoint `/items/` to list every model with details on available fields
  * [x] Return fields configuration (name, type, size)
  * [x] Billing information
* [x] Queryable models as separate Django applications