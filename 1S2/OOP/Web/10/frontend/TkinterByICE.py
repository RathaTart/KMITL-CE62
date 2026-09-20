import tkinter as tk
# from ttkbootstrap import ttk
# from ttkbootstrap.constants import *
from tkinter import *
import requests
import json

# root = ttk.Window(themename='superhero')
root = tk.Tk()
root.option_add("*Font", "impact 20")
root.title("App Pizza")
root.geometry('500x200')

user1_id = StringVar()
face = StringVar()
price = StringVar()
size = StringVar()
quantity = StringVar()

# API_ENDPOINT1 = "http://127.0.0.1:8000/basket/{user_id}"
API_ENDPOINT1 = "http://127.0.0.1:8000/basket/"
API_ENDPOINT1 = "http://127.0.0.1:8000/basket/{}/".format(user1_id.get())

# def on_click():

#     payload = {
#         "user_id": user1_id.get(),
#         "face": face.get(),
#         "price": price.get(),
#         "size": size.get(),
#         "quantity": quantity.get()
#     }
#     response = requests.post(API_ENDPOINT1, json=payload)
#     # if response.ok:
#     #     data = response.json()
#     #     row_count = 6
#     #     data = data['Data']
#     if response.ok:
#         # Label(root, text="Order Compete :"+ str(response.json())).grid(row=8, column=1, padx=5, pady=5)
#         try:
#             data = response.json()
#             Label(root, text="Order Complete: " + str(data)).grid(row=8, column=1, padx=5, pady=5)
#         except json.decoder.JSONDecodeError:
#             Label(root, text="Order Complete: No data returned").grid(row=8, column=1, padx=5, pady=5)
#     else:
#         Label(root, text="Failed to place order").grid(row=8, column=1, padx=5, pady=5)

def on_click():
    payload = {
        "user_id": user1_id.get(),
        "face": face.get(),
        "price": price.get(),
        "size": size.get(),
        "quantity": quantity.get()
}
    payload["user_id"] = str(payload["user_id"])
    payload["face"] = str(payload["face"])
    payload["price"] = str(payload["price"])
    payload["size"] = str(payload["size"])
    payload["quantity"] = str(payload["quantity"])
    try:
        response = requests.post(API_ENDPOINT1, json=payload)
        if response.ok:
            try:
                data = response.json()
                Label(root, text="Order Complete: " + str(data)).grid(row=8, column=1, padx=5, pady=5)
            except json.decoder.JSONDecodeError:
                Label(root, text="Order Complete: No data returned").grid(row=8, column=1, padx=5, pady=5)
        else:
            Label(root, text="Failed to place order").grid(row=8, column=1, padx=5, pady=5)
    except Exception as e:
        Label(root, text="Failed to place order: " + str(e)).grid(row=8, column=1, padx=5, pady=5)
        


Label(root, text="User_ID : ").grid(row=0, column=0, padx=10, ipady=5, sticky='E')
Entry(root, textvariable=user1_id, width=12, justify="left").grid(row=0, column=1, padx=10)

Label(root, text="Face : ").grid(row=1, column=0, padx=10, ipady=5, sticky='E')
Entry(root, textvariable=face, width=12, justify="left").grid(row=1, column=1, padx=10)

Label(root, text="Price : ").grid(row=2, column=0, padx=10, ipady=5, sticky='E')
Entry(root, textvariable=price, width=12, justify="left").grid(row=2, column=1, padx=10)

Label(root, text="Size(S,M,L) : ").grid(row=3, column=0, padx=10, ipady=5, sticky='E')
Entry(root, textvariable=size, width=12, justify="left").grid(row=3, column=1, padx=10)

Label(root, text="Quantity : ").grid(row=4, column=0, padx=10, ipady=5, sticky='E')
Entry(root, textvariable=quantity, width=12, justify="left").grid(row=4, column=1, padx=10)

Button(root, text=" Order!!! ", bg="green", command=on_click).grid(row=5, column=0, columnspan=2)

# def clicker():
#     my_label.config(text=my_topping.get())

# toppings = ["pepperoni","Cheese","Veggie"]
# my_topping = tk.StringVar()

# for topping in toppings:
#     ttk.Radiobutton(root, bootstyle="danger", variable=my_topping, text=topping,
#                     value=topping).pack(side="left",padx=5,pady=5)
    
# my_button = ttk.Button(root, text="select", bootstyle="info", command=clicker)
# my_button.pack(side="left",padx=10,pady=5)

# my_label = ttk.Label(root, text="", font=("Helvetica",14))
# my_label.pack(side="left",padx=10)

# r = requests.get('http://127.0.0.1:8000/docs#/Basket/add_to_basket_basket__user_id__post')
# print(r)

root.mainloop()