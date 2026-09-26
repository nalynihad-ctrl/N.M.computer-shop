export default function RatingStars({ rating = 0, showValue = false }) {
  const stars = Array.from({ length: 5 }, (_, i) => {
    const value = rating - i;
    return value >= 1 ? "★" : value >= 0.5 ? "⯨" : "☆";
  });
  return (
    <span className="rating" aria-label={`Rating ${rating} out of 5`}>
      <span className="stars" aria-hidden="true">
        {stars.join("")}
      </span>
      {showValue && <span className="rating-value">{rating.toFixed(1)}</span>}
    </span>
  );
}