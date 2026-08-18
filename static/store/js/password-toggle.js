/* Reusable password visibility control. It enhances every password field,
 * including fields inserted later by a formset or another script. */
(function () {
    "use strict";

    function addToggle(input) {
        if (input.dataset.passwordToggleBound === "true") return;

        input.dataset.passwordToggleBound = "true";
        input.autocomplete = input.autocomplete || "current-password";

        const wrapper = document.createElement("span");
        wrapper.className = "password-toggle-field";
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        const button = document.createElement("button");
        button.type = "button";
        button.className = "password-toggle";
        button.setAttribute("aria-label", "Show password");
        button.setAttribute("aria-pressed", "false");
        button.title = "Show password";
        button.textContent = "👁";

        button.addEventListener("click", function () {
            const isHidden = input.type === "password";
            input.type = isHidden ? "text" : "password";
            button.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
            button.setAttribute("aria-pressed", String(isHidden));
            button.title = isHidden ? "Hide password" : "Show password";
            input.focus();
        });
        wrapper.appendChild(button);
    }

    function enhancePasswordFields(root) {
        if (root.matches && root.matches('input[type="password"]')) addToggle(root);
        root.querySelectorAll && root.querySelectorAll('input[type="password"]').forEach(addToggle);
    }

    function start() {
        enhancePasswordFields(document);
        new MutationObserver(function (changes) {
            changes.forEach(function (change) {
                change.addedNodes.forEach(function (node) {
                    if (node.nodeType === Node.ELEMENT_NODE) enhancePasswordFields(node);
                });
            });
        }).observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
    else start();
}());
