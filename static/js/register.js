        document.querySelector('form').onsubmit = function(event) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            if (password !== confirmPassword) {
                event.preventDefault();
                alert('Пароли не совпадают');
            }
        };