document.querySelectorAll(".delete-post").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      const response = await fetch(`/delete/${button.dataset.postId}`);
      const result = await response.json();
      if (response.ok && result.status === 1) {
        location.reload();
      } else {
        alert(result.message || "Could not delete post.");
      }
    } catch (error) {
      console.error(error);
      alert("Could not reach the server.");
    }
  });
});
