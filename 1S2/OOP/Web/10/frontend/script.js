// Define pizza data
const pizzas = [
    { name: 'Margherita', price: 8.99 },
    { name: 'Pepperoni', price: 9.99 },
    { name: 'Vegetarian', price: 9.49 }
  ];
  
  // Function to display pizza menu
  function displayMenu() {
    const menu = document.getElementById('menu').querySelector('ul');
    pizzas.forEach(pizza => {
      const listItem = document.createElement('li');
      listItem.textContent = `${pizza.name} - $${pizza.price.toFixed(2)}`;
      menu.appendChild(listItem);
    });
  }
  
  // Function to add pizza to cart
  function addToCart(name, price) {
      // Create a new list item
      const item = document.createElement('li');
      item.textContent = `${name} - $${price.toFixed(2)}`;
  
      // Append the new item to the cart
      const cart = document.getElementById('cartItems');
      cart.appendChild(item);
  }
  
  // Run initialization when the page loads
  window.onload = function() {
    displayMenu();
  };