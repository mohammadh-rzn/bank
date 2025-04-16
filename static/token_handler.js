    // Attach Authorization header to all HTMX requests
    document.addEventListener("DOMContentLoaded", function () {
        htmx.on("configRequest", function (event) {
            const token = localStorage.getItem("access_token");
            if (token) {
                event.detail.headers['Authorization'] = `Bearer ${token}`;
            }
        });
    });

    // Handle 401 errors to attempt refresh
    htmx.on("responseError", async function (evt) {
        if (evt.detail.xhr.status === 401) {
            const refresh = localStorage.getItem("refresh_token");

            if (refresh) {
                try {
                    const res = await fetch("/api/token/refresh/", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ refresh })
                    });

                    if (res.ok) {
                        const data = await res.json();
                        localStorage.setItem("access_token", data.access);
                        console.log("Token refreshed.");
                        // Optionally, retry original request here
                    } else {
                        window.location.href = "/login/";
                    }
                } catch (err) {
                    console.error("Token refresh failed", err);
                    window.location.href = "/login/";
                }
            } else {
                window.location.href = "/login/";
            }
        }
    });