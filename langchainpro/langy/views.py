from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import os
import json
import re


from rest_framework.decorators import api_view
from rest_framework.response import Response

genai.configure(api_key="AIzaSyCNiAbqtP8Sxr8tFAnHQItZTtCB3yZnH_Y")
model = genai.GenerativeModel('gemini-2.0-flash')



user_memory = {
    "name": None,
    "price": None,
    "color": None,
    "fit": None,
    "features": None,
    "gender": None,
    "size": None,
    "brand": None,
    "rating": None,
    "in_stock": None,
    "material": None,
    "occasion": None,
}


def clean_none_fields(memory):
    cleaned = {}
    for key in memory:
        value = memory[key]
        if value is not None:
            cleaned.update({key: value})
    return cleaned


# def update_memory(memory, new_data):
#     memory.update(new_data)



def build_prompt(query):
    return f"""
You are a shopping assistant for an e-commerce hoodie website.

From this user input:
"{query}"

Extract only these filters if mentioned: name, price_max (numerical), price_min (numerical), color, fit, features, gender, size, brand, rating, in_stock, material, occasion.

Respond in this **exact JSON** format:
{{
  "name": "...",
  "color": "...",
  "brand": "...",
  "size": "...",
  "price_max": ...,
  "price_min": ...,
  "fit": "...",
  "feature": "...",
  "gender": "...",
  "rating": ...,
  "in_stock": "...",
  "material": "...",
  "occasion": "..."
}}

Only include fields that are mentioned in the query.
"""



def fetch_data():
    with open ("C:/Users/lookb/Desktop/projects/langchainpro/langy/templates/data.json", mode="r") as f:
        data = json.load(f)
        return data


def filter_products(filters, all_products):
    used_filters = {}
    results = []
    
    for key, value in filters.items():
        if value:
            used_filters[key] = value
    
    for product in all_products:
        valid = True
        
        for key, value in used_filters.items():
            if key == 'price_max':
                if float(product.get('price', 999999)) > float(value):
                    valid = False
            elif key == 'price_min':
                if float(product.get('price', 0)) < float(value):
                    valid = False
            else:
                if key not in product:
                    valid = False
                else:
                    product_value = str(product[key]).lower()
                    filter_value = str(value).lower()
                    if filter_value not in product_value:
                        valid = False

                        if not valid:
                            break
        
        if valid:
            results.append(product)
    
    return {'data': results, 'filters': used_filters}

def home(request):
    data = fetch_data()

    return render(request ,  "index2.html" ,context= {"data":data})


@csrf_exempt
def ai_filter(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            query = data.get("query", "")
            
            if not query:
                return JsonResponse({"error": "No query provided"}, status=400)

            # First AI call to extract filters
            prompt = build_prompt(query)
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            match = re.search(r'\{[\s\S]*\}', raw_text)

            if match:
                raw_json = match.group()
                parsed = json.loads(raw_json)
                user_memory.update(parsed)

                filters = clean_none_fields(user_memory)
                product_data = fetch_data()

                # Second AI call to filter products
                result = filter_products(filters, product_data)
                return JsonResponse(result)
            
            return JsonResponse({"data": []})
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)


@csrf_exempt
def remove_filter(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            filter_text = data.get('filter')
            print(filter_text)
            if not filter_text or ':' not in filter_text:
                return JsonResponse({'error': 'Invalid filter format'}, status=400)

            filter_key = filter_text.split(':')[0].strip().lower()
            user_memory[filter_key] = None

            filters = clean_none_fields(user_memory)
            product_data = fetch_data()
            result = filter_products(filters, product_data)

            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)