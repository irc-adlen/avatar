// Switch to database
db = db.getSiblingDB("cpe_assistant_db");

// Insert base data only if they do not already exist
db.people.updateOne(
  { name: "Mathis" },
  {
    $setOnInsert: {
      name: "Mathis",
      promo: "5IRC",
      image_path: "./faces/mathis.jpeg"
    }
  },
  { upsert: true }
);

db.people.updateOne(
  { name: "Clem" },
  {
    $setOnInsert: {
      name: "Clem",
      promo: "4IRC",
      image_path: "./faces/clem.jpeg"
    }
  },
  { upsert: true }
);
