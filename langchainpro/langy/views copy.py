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

    
# def build_filtering_prompt(filters, product_data):
#     return f"""
# You are a product filtering assistant for a hoodie e-commerce store.

# Here are the filters the user has applied:
# {json.dumps(filters, indent=2)}

# Here is the available product list:
# {json.dumps(product_data, indent=2)}

# Please return a filtered JSON list of products that match **all** the user's filters.
# """


def build_filtering_prompt(filters, product_data):
    return f"""
You are a strict product filtering assistant for a hoodie e-commerce store.

Your job is to filter products based on the exact filters provided by the user.

❗ IMPORTANT:
- You must only include products that match **ALL** the filters exactly.
- If no product matches every filter, return an **empty list**: `[]`
- Do NOT include close matches, partial matches, or suggestions.
- Do NOT relax the filters under any condition.
- Only respond with a valid JSON list of matching products.

User-applied filters:
{json.dumps(filters, indent=2)}

Available product list:
{json.dumps(product_data, indent=2)}

Now return ONLY the list of matching products that meet **every single filter**.
Format the output as a JSON array like this:
[
  {{ "id": ..., "name": ..., ... }}
]
"""


def home(request):
    data = fetch_data()

    return render(request ,  "index2.html" ,context= {"data":data})



# @csrf_exempt      
# def ai_filter(request):
#     if request.method == "POST":
#         query = request.POST.get("query", "")
#         if not query:
#             return HttpResponseBadRequest("No query provided.")

#         try:
#             prompt = build_prompt(query)
#             response = model.generate_content(prompt)
#             raw_text = response.text.strip()
#             match = re.search(r'\{[\s\S]*\}', raw_text)

#             if match:
#                 raw_json = match.group()
#                 parsed = json.loads(raw_json)
#                 user_memory.update(parsed)

#                 filters = clean_none_fields(user_memory)
#                 product_data = fetch_data()

#                 second_prompt = build_filtering_prompt(filters, product_data)
#                 response2 = model.generate_content(second_prompt)

#                 match2 = re.search(r'\[.*\]', response2.text.strip(), re.DOTALL)
#                 filtered_products = json.loads(match2.group()) if match2 else []

#                 return render(request, "index.html", context={"data": filtered_products , "filters": filters})
#             else:
#                 return render(request, "index.html", context={"data": []})
#         except Exception as e:
#             return render(request, "index.html", context={"error": str(e), "data": []})

#     return HttpResponseBadRequest("Invalid method")


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
                second_prompt = build_filtering_prompt(filters, product_data)
                response2 = model.generate_content(second_prompt)

                match2 = re.search(r'\[.*\]', response2.text.strip(), re.DOTALL)
                filtered_products = json.loads(match2.group()) if match2 else []

                return JsonResponse({
                    "data": filtered_products,
                    "filters": filters
                })
            
            return JsonResponse({"data": []})
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)



# def get_products(request):
#     products = [
#         {"name": "Hoodie", "price": 1500, "image": "https://file.aiquickdraw.com/imgcompressed/img/compressed_f8769206cd169f1edea6929c085e5cc1.webp"},
#         {"name": "Cap", "price": 500, "image": "https://file.aiquickdraw.com/imgcompressed/img/compressed_f8769206cd169f1edea6929c085e5cc1.webp"},
#         {"name": "Sneakers", "price": 2500, "image": "https://file.aiquickdraw.com/imgcompressed/img/compressed_f8769206cd169f1edea6929c085e5cc1.webp"},
#     ]
#     return JsonResponse(products, safe=False)