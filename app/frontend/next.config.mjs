/** @type {import('next').NextConfig} */
const nextConfig = {
  // Docker đặt NEXT_OUTPUT=standalone để đóng gói gọn; chạy local / Vercel dùng chế độ thường (`next start` chạy được)
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
  webpack: (config) => {
    // react-pdf/pdfjs tham chiếu "canvas" (chỉ dùng trên Node) — trình duyệt không cần
    config.resolve.alias.canvas = false;
    return config;
  },
};

export default nextConfig;
