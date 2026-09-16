document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("textarea").forEach((textarea) => {
    if (textarea.dataset.emojiReady !== "true") {
      textarea.dataset.emojiReady = "true";
      const toolbar = document.createElement("div");
      toolbar.className = "emoji-toolbar";
      const button = document.createElement("button");
      button.type = "button";
      button.className = "emoji-toggle";
      button.setAttribute("aria-label", "Ouvrir le clavier d'emojis");
      button.innerHTML = '<svg class="ui-icon" aria-hidden="true"><use href="#icon-smile"></use></svg>';
      const picker = document.createElement("emoji-picker");
      picker.className = "emoji-picker";
      picker.setAttribute("aria-label", "Clavier d'emojis");
      picker.setAttribute("data-source", "https://cdn.jsdelivr.net/npm/emoji-picker-element-data@1.8.0/en/emojibase/data.json");
      picker.addEventListener("emoji-click", (event) => {
        const emoji = event.detail.unicode;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        textarea.setRangeText(emoji, start, end, "end");
        textarea.focus();
        picker.classList.remove("emoji-picker--open");
        button.setAttribute("aria-expanded", "false");
      });
      button.addEventListener("click", () => {
        const isOpen = picker.classList.toggle("emoji-picker--open");
        button.setAttribute("aria-expanded", String(isOpen));
      });
      toolbar.append(button, picker);
      textarea.parentNode.insertBefore(toolbar, textarea.nextSibling);
    }
  });

  const themeToggle = document.querySelector("[data-theme-toggle]");
  const applyTheme = (theme) => {
    document.body.classList.toggle("theme-dark", theme === "dark");
    themeToggle?.setAttribute("aria-label", theme === "dark" ? "Activer le mode clair" : "Activer le mode sombre");
  };
  const savedTheme = localStorage.getItem("sa-chat-theme");
  const initialTheme = document.body.classList.contains("theme-dark") ? "dark" : "light";
  applyTheme(savedTheme || initialTheme);
  themeToggle?.addEventListener("click", () => {
    const nextTheme = document.body.classList.contains("theme-dark") ? "light" : "dark";
    localStorage.setItem("sa-chat-theme", nextTheme);
    applyTheme(nextTheme);
  });

  document.querySelectorAll("textarea[data-send-on-enter]").forEach((textarea) => {
    textarea.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        textarea.form?.requestSubmit();
      }
    });
  });

  document.querySelectorAll("[data-reaction-form]").forEach((form) => {
    const reactionButton = form.querySelector("[data-reaction-toggle]");
    const menu = form.querySelector("[data-reaction-menu]");
    const hiddenInput = form.querySelector("input[name='reaction_type']");
    const countNode = form.closest(".post-card")?.querySelector(".post-metrics span:first-child");

    const reactionMap = {
      like: { emoji: "👍", label: "J'aime", css: "reaction--like" },
      love: { emoji: "❤️", label: "J'adore", css: "reaction--love" },
      haha: { emoji: "😂", label: "Haha", css: "reaction--haha" },
      wow: { emoji: "😮", label: "Waouh", css: "reaction--wow" },
      sad: { emoji: "😢", label: "Triste", css: "reaction--sad" },
      angry: { emoji: "😡", label: "En colère", css: "reaction--angry" },
    };

    const openMenu = () => {
      if (!menu) return;
      menu.classList.add("is-open");
      reactionButton?.setAttribute("aria-expanded", "true");
    };

    const closeMenu = () => {
      if (!menu) return;
      menu.classList.remove("is-open");
      reactionButton?.setAttribute("aria-expanded", "false");
    };

    const updateButtonLabel = (value, liked) => {
      const selected = reactionMap[value] || reactionMap.like;
      if (reactionButton) {
        reactionButton.innerHTML = `<span class="reaction-emoji">${selected.emoji}</span><span>${liked ? selected.label : "J'aime"}</span>`;
        reactionButton.classList.remove(...Object.values(reactionMap).map((entry) => entry.css));
        if (liked && selected.css) reactionButton.classList.add(selected.css);
      }
      if (hiddenInput) hiddenInput.value = value || "like";
    };

    reactionButton?.addEventListener("mouseenter", openMenu);
    reactionButton?.addEventListener("focus", openMenu);
    reactionButton?.addEventListener("click", (event) => {
      event.preventDefault();
      if (menu?.classList.contains("is-open")) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    form.addEventListener("mouseleave", () => {
      setTimeout(() => {
        if (!form.matches(":hover") && !menu?.matches(":hover")) {
          closeMenu();
        }
      }, 120);
    });

    menu?.addEventListener("mouseenter", openMenu);
    menu?.addEventListener("mouseleave", () => {
      setTimeout(() => {
        if (!form.matches(":hover") && !menu.matches(":hover")) {
          closeMenu();
        }
      }, 120);
    });

    menu?.querySelectorAll("[data-reaction]").forEach((option) => {
      option.addEventListener("click", async (event) => {
        event.preventDefault();
        const nextValue = option.dataset.reaction || "like";
        hiddenInput.value = nextValue;
        closeMenu();
        form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
      });
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!hiddenInput) return;

      const button = form.querySelector("[data-reaction-toggle]");
      if (button) button.disabled = true;

      try {
        const response = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-CSRFToken": form.querySelector("[name='csrfmiddlewaretoken']").value,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams(new FormData(form)).toString(),
        });

        if (!response.ok) throw new Error("La réaction n'a pas pu être enregistrée.");

        const data = await response.json();
        const countValue = Number(data.count || 0);
        if (countNode) {
          countNode.textContent = `${countValue} réaction${countValue > 1 ? 's' : ''}`;
        }

        updateButtonLabel(data.reaction || hiddenInput.value || "like", Boolean(data.liked));
      } catch (error) {
        window.alert(error.message || "La réaction n'a pas pu être enregistrée.");
      } finally {
        if (button) button.disabled = false;
      }
    });

    updateButtonLabel(hiddenInput?.value || "like", false);
  });

  document.querySelectorAll("[data-comment-toggle]").forEach((button) => {
    const panel = button.closest(".post-card")?.querySelector("[data-comment-panel]");
    button.addEventListener("click", () => {
      if (!panel) return;
      const shouldOpen = panel.hasAttribute("hidden");
      panel.toggleAttribute("hidden", !shouldOpen);
      button.setAttribute("aria-expanded", String(shouldOpen));
    });
  });

  document.querySelectorAll("[data-comment-close]").forEach((button) => {
    button.addEventListener("click", () => {
      const panel = button.closest("[data-comment-panel]");
      const trigger = button.closest(".post-card")?.querySelector("[data-comment-toggle]");
      panel?.setAttribute("hidden", "hidden");
      trigger?.setAttribute("aria-expanded", "false");
    });
  });

  document.querySelectorAll("[data-comment-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const textarea = form.querySelector("textarea[name='content']");
      const content = textarea?.value.trim();
      if (!content) return;

      const submitButton = form.querySelector("button[type='submit']");
      submitButton.disabled = true;
      try {
        const response = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-CSRFToken": form.querySelector("[name='csrfmiddlewaretoken']").value,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: new URLSearchParams(new FormData(form)).toString(),
          redirect: "manual",
        });

        if (!response.ok && response.status !== 302) {
          throw new Error("Le commentaire n'a pas pu être publié.");
        }

        const list = form.closest(".comments-panel")?.querySelector(".comment-list");
        const emptyState = list?.querySelector(".muted-note");
        if (emptyState) emptyState.remove();

        const item = document.createElement("article");
        item.className = "comment-item";
        item.innerHTML = `
          <div class="comment-item__meta">
            <strong>Vous</strong>
            <small>À l'instant</small>
          </div>
          <p>${content}</p>
        `;
        list?.prepend(item);

        const metrics = form.closest(".post-card")?.querySelectorAll(".post-metrics span");
        if (metrics && metrics[1]) {
          const match = metrics[1].textContent.match(/\d+/);
          const current = match ? Number(match[0]) : 0;
          metrics[1].textContent = `${current + 1} commentaire${current + 1 > 1 ? 's' : ''}`;
        }

        textarea.value = "";
      } catch (error) {
        window.alert(error.message || "Le commentaire n'a pas pu être publié.");
      } finally {
        submitButton.disabled = false;
      }
    });
  });

  document.querySelectorAll("[data-post-menu-trigger]").forEach((button) => {
    const menu = button.closest(".post-header__menu")?.querySelector("[data-post-menu]");
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      menu?.toggleAttribute("hidden");
    });
  });

  document.addEventListener("click", (event) => {
    document.querySelectorAll("[data-post-menu]").forEach((menu) => {
      if (!menu.contains(event.target) && !menu.previousElementSibling?.contains(event.target)) {
        menu.setAttribute("hidden", "hidden");
      }
    });
  });

  document.querySelectorAll("[data-share-trigger]").forEach((button) => {
    button.addEventListener("click", () => {
      const panel = button.closest(".post-card")?.querySelector("[data-share-panel]");
      const menu = button.closest("[data-post-menu]");
      menu?.setAttribute("hidden", "hidden");
      if (panel) {
        panel.toggleAttribute("hidden");
      }
    });
  });

  document.querySelectorAll("[data-share-toggle]").forEach((button) => {
    const panel = button.closest(".post-card")?.querySelector("[data-share-panel]");
    button.addEventListener("click", () => {
      panel?.toggleAttribute("hidden");
    });
  });

  document.querySelectorAll("[data-close-share]").forEach((button) => {
    button.addEventListener("click", () => {
      const panel = button.closest("[data-share-panel]");
      panel?.setAttribute("hidden", "hidden");
    });
  });

  document.querySelectorAll("[data-copy-link]").forEach((button) => {
    button.addEventListener("click", async () => {
      const link = button.dataset.copyLink;
      try {
        await navigator.clipboard.writeText(link);
        button.textContent = "Lien copié";
      } catch {
        button.textContent = "Copier le lien";
      }
    });
  });

  const aiForm = document.querySelector("[data-ai-form]");
  const aiConversation = document.querySelector("[data-ai-conversation]");
  const escapeHtml = (value) => String(value).replace(/[&<>]/g, (character) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;"}[character])).replace(/\n/g, "<br>");
  const renderAiHistory = (history) => {
    aiConversation.innerHTML = history.map((item) => `<article class="ai-message ${item.role === "user" ? "ai-message--user" : "ai-message--assistant"}"><div class="ai-message__badge">${item.role === "user" ? "V" : "S"}</div><div><small>${item.role === "user" ? "Vous" : "Sacha AI"}</small><p>${escapeHtml(item.text)}</p></div></article>`).join("");
  };
  aiForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const textarea = aiForm.querySelector("textarea[name='message']");
    const button = aiForm.querySelector("button[type='submit']");
    const message = textarea.value.trim();
    if (!message) return;
    button.disabled = true;
    const thinking = document.createElement("article");
    thinking.className = "ai-message ai-message--assistant ai-thinking";
    thinking.innerHTML = '<div class="ai-message__badge">S</div><div><small>Sacha AI</small><p>Sacha AI réfléchit...</p></div>';
    aiConversation.append(thinking);
    try {
      const response = await fetch(aiForm.action, {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRFToken": aiForm.querySelector("[name='csrfmiddlewaretoken']").value},
        body: JSON.stringify({message, conversation_id: aiConversation.dataset.conversationId || null}),
      });
      let data;
      try { data = await response.json(); } catch { throw new Error("Réponse invalide du serveur."); }
      if (!response.ok) throw new Error(data.error || "Une erreur est survenue.");
      aiConversation.dataset.conversationId = data.conversation_id;
      renderAiHistory(data.history);
      textarea.value = "";
      aiConversation.lastElementChild?.scrollIntoView({behavior: "smooth", block: "nearest"});
    } catch (error) {
      thinking.remove();
      window.alert(error.message);
    } finally {
      button.disabled = false;
      textarea.focus();
    }
  });

  document.querySelector("[data-ai-clear]")?.addEventListener("click", async () => {
    if (!window.confirm("Effacer cette conversation ?")) return;
    const csrfToken = aiForm.querySelector("[name='csrfmiddlewaretoken']").value;
    const body = new URLSearchParams({csrfmiddlewaretoken: csrfToken, conversation_id: aiConversation.dataset.conversationId || ""});
    let response;
    try {
      response = await fetch(aiForm.dataset.clearEndpoint, {method: "POST", headers: {"X-CSRFToken": csrfToken}, body});
    } catch {
      return window.alert("Impossible de joindre le serveur.");
    }
    if (!response.ok) return window.alert("Impossible d'effacer la conversation.");
    aiConversation.dataset.conversationId = "";
    aiConversation.innerHTML = '<div class="ai-empty"><div class="ai-empty__icon"><svg class="ui-icon"><use href="#icon-ai"></use></svg></div><h2>Commencez une conversation</h2><p>Sacha AI est pret a vous aider.</p></div>';
  });

  document.addEventListener("click", (event) => {
    document.querySelectorAll(".emoji-picker--open").forEach((picker) => {
      if (!picker.parentNode.contains(event.target)) picker.classList.remove("emoji-picker--open");
    });
  });

  const toggle = document.querySelector(".menu-toggle");
  const menu = document.querySelector(".mobile-menu");

  if (toggle && menu) {
    toggle.addEventListener("click", () => {
      const isOpen = menu.classList.toggle("mobile-menu--open");
      toggle.setAttribute("aria-expanded", String(isOpen));
    });
  }

  document.querySelectorAll("[data-confirm]").forEach((element) => {
    element.addEventListener("click", (event) => {
      if (!window.confirm(element.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = document.getElementById(button.dataset.passwordToggle);
      if (!input) return;
      const visible = input.type === "text";
      input.type = visible ? "password" : "text";
      button.setAttribute("aria-label", visible ? "Afficher le mot de passe" : "Masquer le mot de passe");
      button.innerHTML = `<svg class="ui-icon" aria-hidden="true"><use href="#icon-${visible ? "eye" : "eye-off"}"></use></svg>`;
    });
  });

  const liveSearchForm = document.querySelector("[data-live-search-form]");
  const liveSearchResults = document.querySelector("[data-live-search-results]");
  const liveSearchInput = liveSearchForm?.querySelector("input[name='q']");
  let searchTimer;
  liveSearchInput?.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(async () => {
      const query = liveSearchInput.value.trim();
      if (!query) { liveSearchResults.innerHTML = ""; return; }
      const response = await fetch(`${liveSearchForm.dataset.searchEndpoint}?q=${encodeURIComponent(query)}`, {headers: {"X-Requested-With": "XMLHttpRequest"}});
      if (!response.ok) return;
      const data = await response.json();
      liveSearchResults.innerHTML = data.results.map((result) => `<a class="btn btn-secondary btn-small" href="${result.url}">${result.username}</a>`).join("");
    }, 250);
  });
});
