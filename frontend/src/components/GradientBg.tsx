import React, { useMemo } from "react";

const Gradient3DBackground = ({
  width = 30,
  height = 30,
  seed = 0,
  radius = 999,
}) => {
  const gradientStyle = useMemo(() => {
    // Generate random values based on the seed
    const random = (seed: number) => {
      const x = Math.sin(seed) * 10000;
      return x - Math.floor(x);
    };

    const hue1 = Math.floor(random(seed) * 360);
    const hue2 = Math.floor(random(seed + 1) * 360);
    const hue3 = Math.floor(random(seed + 2) * 360);

    return {
      width: `${width}px`,
      height: `${height}px`,
      background: `
        linear-gradient(
          135deg,
          hsl(${hue1}, 100%, 60%) 0%,
          hsl(${hue2}, 100%, 60%) 50%,
          hsl(${hue3}, 100%, 60%) 100%
        )
      `,
      borderRadius: radius + "px",
      boxShadow: `
        0 10px 20px rgba(0, 0, 0, 0.19),
        0 6px 6px rgba(0, 0, 0, 0.23),
        inset 0 -5px 10px rgba(255, 255, 255, 0.5),
        inset 0 5px 10px rgba(0, 0, 0, 0.2)
      `,
      position: "relative",
      overflow: "hidden",
    };
  }, [width, height, seed, radius]);

  const shineStyle = {
    position: "absolute",
    top: "-50%",
    left: "-50%",
    right: "-50%",
    bottom: "-50%",
    background:
      "radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 60%)",
    transform: "rotate(30deg)",
    opacity: 0.7,
  };
  return (
    <div style={gradientStyle as React.CSSProperties}>
      <div style={shineStyle as React.CSSProperties} />
    </div>
  );
};

export default Gradient3DBackground;
