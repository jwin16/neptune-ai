// src/lib/api.ts
export const sendMessage = async (messages: { role: "user" | "assistant"; content: string }[]) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ messages }),
      });
  
      if (!res.ok) {
        console.error("Error:", res.status, res.statusText);
        throw new Error("Failed to send message");
      }
  
      const data = await res.json();
      return data.reply;
    } catch (err) {
      console.error("Error during fetch:", err);
      throw err;
    }
  };