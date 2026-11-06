from django.shortcuts import render

def indexfile(request):
    return render(request, 'index.html')

def beauty(request):
    return render(request, 'beauty.html')

def electronics(request):
    return render(request, 'electronics.html')

def gifting(request):
    return render(request, 'gifting.html')

def kids(request):
    return render(request, 'kids.html')

def pharmacy(request):
    return render(request, 'pharmacy.html')
    
def meat(request):
    return render(request, 'meat.html')    

def fruits(request):
    return render(request, 'fruits.html')  

def Grocery(request):
    return render(request, 'Grocery.html')      

def profile(request):
    return render(request, 'profile.html')

from django.shortcuts import render

def search(request):
    query = request.GET.get('q', '')

    products = [
        # Electronics
        "Samsung Galaxy M35",
        "HP Laptop",
        "Boat Headphones",
        "Noise Smart Watch",
        "Gaming Mouse",
        "Bluetooth Speaker",

        # Beauty
        "Himalaya Face Wash",
        "Dove Shampoo",
        "Nivea Soft Cream",
        "Lakme Lipstick",
        "Perfume",

        # Pharmacy
        "Paracetamol 650",
        "Vitamin C Tablets",
        "Dettol Sanitizer",
        "Band Aid Pack",
        "Digital Thermometer",

        # Grocery
        "Amul Milk",
        "Brown Bread",
        "Butter",
        "Paneer",
        "Basmati Rice",
        "Aashirvaad Atta",
        "Toor Dal",

        # Fruits
        "Apple",
        "Banana",
        "Orange",
        "Mango",
        "Grapes",
        "Kiwi",
        "Pineapple",
        "Pomegranate",

        # Meat
        "Chicken Curry Cut",
        "Chicken Breast",
        "Mutton Curry Cut",
        "Fresh Fish",
        "Prawns",
        "Eggs",

        # Kids
        "Teddy Bear",
        "Remote Control Car",
        "Building Blocks",
        "School Bag",
        "Color Box",

        # Gifting
        "Chocolate Hamper",
        "Dry Fruit Box",
        "Red Roses Bouquet",
        "Gift Mug",
        "Photo Frame"
    ]

    results = []

    if query:
        for product in products:
            if query.lower() in product.lower():
                results.append(product)

    return render(request, 'search.html', {
        'query': query,
        'results': results
    })