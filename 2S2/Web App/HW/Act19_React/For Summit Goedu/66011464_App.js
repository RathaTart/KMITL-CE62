import React, { useState } from "react";
import "./styles.css";

const FoodItem = ({ type, name, description, image, onVoteChange }) => {
  const [voteCount, setVoteCount] = useState(0);

  const handleVote = () => {
    if (voteCount < 10) {
      const newCount = voteCount + 1;
      setVoteCount(newCount);
      onVoteChange(name, newCount); // 🔹 Send data to parent
    } else {
      alert("Cannot Vote more");
    }
  };

  const handleUnvote = () => {
    if (voteCount > 0) {
      const newCount = voteCount - 1;
      setVoteCount(newCount);
      onVoteChange(name, newCount); // 🔹 Send data to parent
    } else {
      alert("Cannot unvote");
    }
  };

  return (
    <div className="food-item">
      <div className="food-content">
        <div className="food-text">
          <h2 className="food-type">{type}</h2>
          <h3 className="food-title">{name}</h3>
          <p>{description}</p>
        </div>
        <div className="food-image-container">
          <img src={image} alt={name} className="food-image" />
        </div>
      </div>
      <div className="vote-section">
        <button onClick={handleVote} className="vote-button">Click to Vote</button>
        <span className={voteCount === 0 ? "min" : voteCount === 10 ? "max" : "normal"}>
          {voteCount === 10 ? "MAX" : voteCount === 0 ? "MIN" : voteCount}
        </span>
        <button onClick={handleUnvote} className="unvote-button">Click to Unvote</button>
      </div>
    </div>
  );
};

const App = () => {
  const [votes, setVotes] = useState({});

  const handleVoteChange = (foodName, newVoteCount) => {
    setVotes((prevVotes) => ({
      ...prevVotes,
      [foodName]: newVoteCount,
    }));
  };

  const foodItems = [
    {
      type_of_food: "อาหารคาว",
      food_name: "ข้าวผัด",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec id lacinia nulla. Morbi vel rutrum quam, venenatis pharetra nisi. Pellentesque condimentum urna eros, quis faucibus nibh pulvinar sed. Vestibulum aliquet vitae nibh eu feugiat. Integer tincidunt, turpis venenatis vehicula consectetur, mauris est cursus sem, ac euismod neque elit ut felis. Sed porta lorem sapien, vitae dignissim nulla pulvinar sed.",
      image: "https://images.deliveryhero.io/image/fd-th/LH/qhs9-listing.jpg"
    },
    {
      type_of_food: "อาหารหวาน",
      food_name: "บัวลอย",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec id lacinia nulla. Morbi vel rutrum quam, venenatis pharetra nisi. Pellentesque condimentum urna eros, quis faucibus nibh pulvinar sed. Vestibulum aliquet vitae nibh eu feugiat. Integer tincidunt, turpis venenatis vehicula consectetur, mauris est cursus sem, ac euismod neque elit ut felis. Sed porta lorem sapien, vitae dignissim nulla pulvinar sed.",
      image: "https://chefoldschool.com/wp-content/uploads/2023/04/1-1.jpg"
    }
  ];

  return (
    <>
      <h1 className="title">โหวตอาหาร</h1>
      <div className="food-list">
        {foodItems.map((food, index) => (
          <FoodItem
            key={index}
            type={food.type_of_food}
            name={food.food_name}
            description={food.description}
            image={food.image}
            onVoteChange={handleVoteChange} // 🔹 Pass callback function
          />
        ))}
      </div>
      <div className="vote-summary">
        <h2>Vote Summary</h2>
        {Object.entries(votes).map(([foodName, count]) => (
          <p key={foodName}>{foodName}: {count} votes</p>
        ))}
      </div>
    </>
  );
};

export default App;
