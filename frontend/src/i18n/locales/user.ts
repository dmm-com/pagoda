import { defineMessages } from "../defineMessages";

export const userMessages = defineMessages({
  ja: {
    // ChangeUserAuthModal
    "user.changeAuthModal.title": "LDAP への認証方法の変更",
    "user.changeAuthModal.description":
      '認証を LDAP のパスワードで行うことができます。（注：ユーザ "{{username}}" が LDAPに登録されていない場合は変更できません）',
    "user.changeAuthModal.updateSuccess": "認証方法の変更に成功しました",
    "user.changeAuthModal.updateFailure": "認証方法の変更に失敗しました",

    // PasswordResetConfirmModal
    "user.passwordResetConfirmModal.title": "パスワードリセット",
    "user.passwordResetConfirmModal.description":
      "新しいパスワードを入力してください。",
    "user.passwordResetConfirmModal.resetSuccess":
      "パスワードリセットに成功しました",
    "user.passwordResetConfirmModal.resetFailure":
      "パスワードリセットに失敗しました",

    // PasswordResetModal
    "user.passwordResetModal.title": "パスワードリセット",
    "user.passwordResetModal.description":
      "パスワードリセットをメールで案内します。ユーザ名を入力してください。",
    "user.passwordResetModal.sendSuccess":
      "パスワードリセットメールの送信に成功しました",
    "user.passwordResetModal.sendFailure":
      "パスワードリセットメールの送信に失敗しました",

    // UserControlMenu
    "user.controlMenu.editPassword": "パスワード編集",
    "user.controlMenu.deleteConfirm": "本当に削除しますか？({{username}})",
    "user.controlMenu.deleteSuccess":
      "ユーザ({{username}})の削除が完了しました",
    "user.controlMenu.deleteFailure": "ユーザの削除が失敗しました",

    // UserForm
    "user.form.authMethod": "認証方法",
    "user.form.localAuth": "ローカル認証",
    "user.form.changeToLdap": "認証方法をLDAPに変更する",
    "user.form.ldapAuth": "LDAP 認証",
    "user.form.accessTokenExpiry": "アクセストークンの有効期限設定",
    "user.form.tokenLifetimeLabel": "アクセストークンが有効な期間",
    "user.form.secondsUnit": "秒",
    "user.form.tokenLifetimeHelperText":
      "※0 を入力した場合は期限は無期限になります",
    "user.form.tokenCreatedAt": "作成日",
    "user.form.tokenExpiresAt": "有効期限",
    "user.form.tokenUnlimited": "無期限",
    "user.form.accessToken": "アクセストークン",
    "user.form.accessTokenNotIssued": "アクセストークンが発行されていません",
    "user.form.accessTokenPlaceholder":
      "「ACCESS TOKEN をリフレッシュ」ボタンを押して発行してください",
    "user.form.copyTokenSuccess":
      "アクセストークンをクリップボードにコピーしました",
    "user.form.copyTokenFailure": "クリップボードへのコピーに失敗しました",
    "user.form.email": "メールアドレス",
    "user.form.emailPlaceholder": "メールアドレスを入力してください",
    "user.form.name": "名前",
    "user.form.usernamePlaceholder": "ユーザ名を入力してください",
    "user.form.password": "パスワード",
    "user.form.passwordPlaceholder": "パスワードを入力してください",
    "user.form.isSuperuser": "管理者権限",
    "user.form.columnItem": "項目",
    "user.form.columnContent": "内容",
    "user.form.usernameRequired": "ユーザ名は必須です",
    "user.form.emailInvalid": "正しいメールアドレスを入力してください",
    "user.form.passwordRequired": "パスワードは必須です",
    "user.form.tokenLifetimeInvalid": "有効期限には数値を入力してください",
    "user.form.tokenLifetimeNotInteger": "整数を入力してください",
    "user.form.tokenLifetimeMin": "0以上の秒数で入力してください",
    "user.form.belongingGroups": "所属グループ",
    "user.form.inheritedGroupLabel": "{{name}} (継承)",
    "user.form.noBelongingGroups": "所属しているグループはありません",
    "user.form.adminNote": "管理",
    "user.form.viaGroupsNote": "{{names}} 経由",
    "user.form.belongingRoles": "所属ロール",
    "user.form.noBelongingRoles": "所属しているロールはありません",
    "user.form.createdReadOnlyUsers": "作成したRead-Onlyユーザー",

    // UserImportModal
    "user.importModal.title": "ユーザのインポート",
    "user.importModal.description":
      "インポートするファイルを選択してください。",
    "user.importModal.caption": "※CSV形式のファイルは選択できません。",

    // UserList / UserListPage
    "user.list.pageTitle": "ユーザ管理",
    "user.list.searchPlaceholder": "ユーザを絞り込む",
    "user.list.createNew": "新規ユーザを登録",
    "user.list.createReadOnly": "Read-Only ユーザを作成",
    "user.list.passwordChangeSuccess": "パスワードの変更が完了しました",

    // UserPasswordFormModal
    "user.passwordFormModal.title": "パスワード編集",
    "user.passwordFormModal.oldPasswordLabel":
      "今まで使用していたパスワードをご入力ください。",
    "user.passwordFormModal.newPasswordLabel":
      "新しいパスワードをご入力ください。",
    "user.passwordFormModal.confirmPasswordLabel":
      "確認のためもう一度、新しいパスワードをご入力ください。",
    "user.passwordFormModal.mismatch":
      "新しいパスワードと、入力内容が一致しません",
    "user.passwordFormModal.resetFailure":
      "パスワードリセットに失敗しました。入力項目を見直してください",

    // UserEditPage
    "user.edit.pageTitle": "ユーザ情報の設定",
    "user.edit.newUserTitle": "新規ユーザの作成",
    "user.edit.description": "ユーザ編集",
    "user.edit.confirmLeave":
      "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
    "user.edit.loading": "読み込み中...",
    "user.edit.newUserPrefix": "新規作成",
    "user.edit.resetPassword": "パスワードの再設定",
    "user.edit.passwordChanged": "パスワードを変更しました",
    "user.edit.refreshToken": "Access Token をリフレッシュ",
    "user.edit.refreshTokenConfirm":
      "AccessTokenを更新してもよろしいですか？ ※現在入力中の項目はリセットされます",
    "user.edit.tokenUpdateFailureWithReason":
      "Token の更新に失敗しました。詳細: {{reason}}",
    "user.edit.tokenUpdateFailure": "Token の更新に失敗しました。",
    "user.edit.submitFailureDetail": '詳細: "{{message}}"',

    // LoginPage
    "user.login.agreeTerms": "以下の規約に合意する。",
    "user.login.termsLinkLabel": "Pagoda サービス規約",
    "user.login.termsRequired": "ご利用には、サービス規約への合意が必要です。",
    "user.login.invalidCredentials": "ユーザ名またはパスワードが違います。",
    "user.login.ssoLogin": "SSO ログイン",
    "user.login.passwordReset": "パスワードリセット",

    // NonTermsServiceAgreement
    "user.terms.description":
      "ご利用をされるにはサービス規約への同意が必要です。",
    "user.terms.backToAgreement": "規約同意ページに戻る",
  },
  en: {
    // ChangeUserAuthModal
    "user.changeAuthModal.title": "Change authentication method to LDAP",
    "user.changeAuthModal.description":
      'You can authenticate with an LDAP password. (Note: this cannot be changed if the user "{{username}}" is not registered in LDAP)',
    "user.changeAuthModal.updateSuccess":
      "Successfully changed the authentication method",
    "user.changeAuthModal.updateFailure":
      "Failed to change the authentication method",

    // PasswordResetConfirmModal
    "user.passwordResetConfirmModal.title": "Password reset",
    "user.passwordResetConfirmModal.description":
      "Please enter your new password.",
    "user.passwordResetConfirmModal.resetSuccess":
      "Successfully reset the password",
    "user.passwordResetConfirmModal.resetFailure":
      "Failed to reset the password",

    // PasswordResetModal
    "user.passwordResetModal.title": "Password reset",
    "user.passwordResetModal.description":
      "We will guide you through resetting your password by email. Please enter your username.",
    "user.passwordResetModal.sendSuccess":
      "Successfully sent the password reset email",
    "user.passwordResetModal.sendFailure":
      "Failed to send the password reset email",

    // UserControlMenu
    "user.controlMenu.editPassword": "Edit password",
    "user.controlMenu.deleteConfirm":
      "Are you sure you want to delete this? ({{username}})",
    "user.controlMenu.deleteSuccess":
      "Successfully deleted the user ({{username}})",
    "user.controlMenu.deleteFailure": "Failed to delete the user",

    // UserForm
    "user.form.authMethod": "Authentication method",
    "user.form.localAuth": "Local authentication",
    "user.form.changeToLdap": "Change authentication method to LDAP",
    "user.form.ldapAuth": "LDAP authentication",
    "user.form.accessTokenExpiry": "Access token expiration settings",
    "user.form.tokenLifetimeLabel": "Access token validity period",
    "user.form.secondsUnit": "sec",
    "user.form.tokenLifetimeHelperText":
      "* If you enter 0, the token will never expire",
    "user.form.tokenCreatedAt": "Created at",
    "user.form.tokenExpiresAt": "Expires at",
    "user.form.tokenUnlimited": "Never expires",
    "user.form.accessToken": "Access token",
    "user.form.accessTokenNotIssued": "No access token has been issued",
    "user.form.accessTokenPlaceholder":
      'Press the "Refresh ACCESS TOKEN" button to issue one',
    "user.form.copyTokenSuccess": "Copied the access token to the clipboard",
    "user.form.copyTokenFailure": "Failed to copy to the clipboard",
    "user.form.email": "Email address",
    "user.form.emailPlaceholder": "Please enter your email address",
    "user.form.name": "Name",
    "user.form.usernamePlaceholder": "Please enter a username",
    "user.form.password": "Password",
    "user.form.passwordPlaceholder": "Please enter a password",
    "user.form.isSuperuser": "Administrator privileges",
    "user.form.columnItem": "Item",
    "user.form.columnContent": "Content",
    "user.form.usernameRequired": "Username is required",
    "user.form.emailInvalid": "Please enter a valid email address",
    "user.form.passwordRequired": "Password is required",
    "user.form.tokenLifetimeInvalid": "Please enter a number for the lifetime",
    "user.form.tokenLifetimeNotInteger": "Please enter an integer",
    "user.form.tokenLifetimeMin":
      "Please enter a number of seconds of 0 or more",
    "user.form.belongingGroups": "Belonging groups",
    "user.form.inheritedGroupLabel": "{{name}} (inherited)",
    "user.form.noBelongingGroups": "No belonging groups",
    "user.form.adminNote": "Admin",
    "user.form.viaGroupsNote": "via {{names}}",
    "user.form.belongingRoles": "Belonging roles",
    "user.form.noBelongingRoles": "No belonging roles",
    "user.form.createdReadOnlyUsers": "Created Read-Only users",

    // UserImportModal
    "user.importModal.title": "Import users",
    "user.importModal.description": "Please select a file to import.",
    "user.importModal.caption": "* CSV files cannot be selected.",

    // UserList / UserListPage
    "user.list.pageTitle": "User management",
    "user.list.searchPlaceholder": "Filter users",
    "user.list.createNew": "Register a new user",
    "user.list.createReadOnly": "Create a read-only user",
    "user.list.passwordChangeSuccess": "Successfully changed the password",

    // UserPasswordFormModal
    "user.passwordFormModal.title": "Edit password",
    "user.passwordFormModal.oldPasswordLabel":
      "Please enter your current password.",
    "user.passwordFormModal.newPasswordLabel":
      "Please enter your new password.",
    "user.passwordFormModal.confirmPasswordLabel":
      "Please enter your new password again to confirm.",
    "user.passwordFormModal.mismatch":
      "The new password does not match the confirmation",
    "user.passwordFormModal.resetFailure":
      "Failed to reset the password. Please review the entered values",

    // UserEditPage
    "user.edit.pageTitle": "User settings",
    "user.edit.newUserTitle": "Create a new user",
    "user.edit.description": "Edit user",
    "user.edit.confirmLeave":
      "Your edits will be lost. Are you sure you want to leave this page?",
    "user.edit.loading": "Loading...",
    "user.edit.newUserPrefix": "New",
    "user.edit.resetPassword": "Reset password",
    "user.edit.passwordChanged": "Successfully changed the password",
    "user.edit.refreshToken": "Refresh Access Token",
    "user.edit.refreshTokenConfirm":
      "Are you sure you want to refresh the Access Token? * Any currently entered values will be reset",
    "user.edit.tokenUpdateFailureWithReason":
      "Failed to update the token. Details: {{reason}}",
    "user.edit.tokenUpdateFailure": "Failed to update the token.",
    "user.edit.submitFailureDetail": 'Details: "{{message}}"',

    // LoginPage
    "user.login.agreeTerms": "I agree to the following terms.",
    "user.login.termsLinkLabel": "Pagoda Terms of Service",
    "user.login.termsRequired":
      "You must agree to the terms of service to use this.",
    "user.login.invalidCredentials": "Incorrect username or password.",
    "user.login.ssoLogin": "SSO login",
    "user.login.passwordReset": "Password reset",

    // NonTermsServiceAgreement
    "user.terms.description":
      "You must agree to the terms of service to use this.",
    "user.terms.backToAgreement": "Back to the terms agreement page",
  },
});
