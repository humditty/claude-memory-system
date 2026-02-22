# 🔐 GitHub 多账号管理完整指南

解决 "我有多个 GitHub 账号，该如何管理 SSH 和推送？" 的问题

---

## 📋 当前你的情况

```
账号 A: humditty      (目标仓库所有者)
账号 B: whistleditty  (当前 SSH 密钥关联)

✅ 已推送项目：https://github.com/humditty/claude-memory-system
⚠️  SSH 问题：当前 SSH 密钥属于 whistleditty 账号
```

---

## 🎯 两种解决方案

### **方案A：使用 HTTPS（最快，已工作）** ⭐

当前你的项目已经是 HTTPS，**不需要任何配置**，可以直接使用。

**优势**：
- ✅ 不需要 SSH 密钥
- ✅ 自动使用正确的账号凭据
- ✅ 最简单

**工作原理**：
1. HTTPS 推送时 Git 会提示输入 GitHub 用户名和 **Personal Access Token (PAT)**
2. Git Credential Helper 会记住凭据
3. 每个域名（github.com）可以存储多组凭据，Git 会按域名匹配

**配置 HTTPS 凭据管理器**：
```bash
# 缓存凭据（15分钟）
git config --global credential.helper 'cache --timeout=900'

# 或永久存储（推荐 macOS）
git config --global credential.helper osxkeychain

# Windows 用户：
# git config --global credential.helper wincred

# Linux 用户：
# git config --global credential.helper store
```

**首次推送**（如果没配置凭据）：
```bash
# HTTPS URL 已经存在，直接推送
git push origin main

# 会提示：
# Username: humditty
# Password: <输入你的 Personal Access Token>
```

**创建 Personal Access Token**：
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限：`repo` (全部仓库)
4. 复制生成的 token，保存好

---

### **方案B：配置 SSH 多账号（长期推荐）**

让你的本地 SSH 自动为不同仓库使用不同密钥。

#### **步骤1：为 humditty 生成 SSH 密钥**

```bash
# 使用 Ed25519（更现代安全）
ssh-keygen -t ed25519 -C "479876747@qq.com" -f ~/.ssh/id_ed25519_humditty -N ""

# 或使用 RSA 4096
# ssh-keygen -t rsa -b 4096 -C "479876747@qq.com" -f ~/.ssh/id_rsa_humditty -N ""
```

#### **步骤2：添加公钥到 GitHub**

```bash
# 查看公钥内容
cat ~/.ssh/id_ed25519_humditty.pub
# 复制整段内容（以 ssh-ed25519 ... 开头）
```

1. 登录 GitHub (https://github.com)
2. 进入 Settings → SSH and GPG keys → New SSH key
3. Title: `humditty-$(hostname)` 例如：`humditty-macbook`
4. Key: 粘贴刚才的公钥
5. 点击 Add SSH key

**为 whistleditty 也添加公钥**（如果尚未添加）：
```bash
cat ~/.ssh/id_rsa.pub
# 复制并添加到 GitHub（使用 whistleditty 账号登录）
```

#### **步骤3：配置 ~/.ssh/config**

```bash
# 编辑 SSH 配置
nano ~/.ssh/config
```

内容：
```ssh
# 默认 humditty 账号
Host github-humditty
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_humditty
    IdentitiesOnly yes

# whistleditty 账号（如果需要）
Host github-whistleditty
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa
    IdentitiesOnly yes
```

#### **步骤4：切换项目的 remote URL**

```bash
cd /Users/xiuhao/.newmax/workspace

# 查看当前 remote
git remote -v
# origin  https://github.com/humditty/claude-memory-system.git

# 切换为 SSH 别名
git remote set-url origin github-humditty:humditty/claude-memory-system.git

# 验证
git remote -v
# origin  github-humditty:humditty/claude-memory-system.git (fetch)
# origin  github-humditty:humditty/claude-memory-system.git (push)
```

#### **步骤5：测试连接**

```bash
# 测试 humditty 账号
ssh -T git@github-humditty
# 预期输出：Hi humditty! You've successfully authenticated...

# 测试 whistleditty 账号
ssh -T git@github-whistleditty
# 预期输出：Hi whistleditty! You've successfully authenticated...
```

#### **步骤6：推送**

```bash
git push origin main
# 现在会自动使用 ~/.ssh/id_ed25519_humditty 密钥
# 以 humditty 账号认证
```

---

## 🏗️ 多项目使用不同账号

### **项目 A（个人项目，用 humditty）**

```bash
cd ~/projects/personal/project-a

# 设置 remote 使用 humditty 别名
git remote set-url origin github-humditty:humditty/project-a.git

# 配置 Git 用户（项目级，不覆盖全局）
git config user.name "humditty"
git config user.email "479876747@qq.com"
```

### **项目 B（工作项目，用 work-account）**

```bash
cd ~/projects/work/project-b

# 需要先创建 work-account 的 SSH 密钥和 GitHub 添加
git remote set-url origin github-work:work-account/project-b.git

# 配置工作账号
git config user.name "work-account"
git config user.email "work@company.com"
```

**查看项目级配置**：
```bash
git config --local user.name
git config --local user.email
git remote -v
```

**取消项目级配置，恢复全局**：
```bash
git config --unset user.name
git config --unset user.email
# 会回退到 global 配置
```

---

## 🎯 针对你当前项目的最佳建议

### **立即可以做的（3分钟内完成）**：

**方案1：保持 HTTPS（最简单）**
```bash
# 你的项目当前已经是 HTTPS，已经可以工作了！
# 只需确保设置了凭据助手：

git config --global credential.helper osxkeychain  # macOS
# 或
git config --global credential.helper cache         # Linux

# 下次 git push 会提示输入：
# Username: humditty
# Password: <你的 GitHub Personal Access Token>
```

**方案2：切换到 SSH（推荐长期使用）**

1. **生成 humditty 的 SSH 密钥**：
```bash
bash .generate-humditty-key.sh
# 复制输出的公钥
```

2. **添加到 GitHub**：
   - 访问 https://github.com/settings/keys
   - 使用 humditty 账号登录
   - 粘贴公钥，Title 填 "humditty-mac"

3. **切换项目 remote**：
```bash
cd /Users/xiuhao/.newmax/workspace
git remote set-url origin github-humditty:humditty/claude-memory-system.git
```

4. **测试**：
```bash
ssh -T git@github-humditty
# 应该显示：Hi humditty!

git push origin main
# 应该成功推送，不再需要密码
```

---

## 🔧 故障排除

### **问题1：`Permission denied (publickey)`**

```bash
# 调试 SSH 连接
ssh -vT git@github-humditty

# 检查密钥是否正确加载
ssh-add -l

# 如果需要，添加密钥到代理
ssh-add ~/.ssh/id_ed25519_humditty
```

### **问题2：`fatal: The requested URL returned error: 403`**

HTTPS 权限问题，检查：
```bash
# 清除旧凭据
git credential-osxkeychain erase
# 或手动删除 Keychain Access 中的 github.com 条目

# 重新推送，输入正确的 token
git push origin main
```

### **问题3：`.ssh/config` 不生效**

```bash
# 检查文件权限
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/id_*
ls -la ~/.ssh/

# 确保配置文件在最前面
# 如果有 Include 指令（如 OrbStack），确保你的 Host 配置在其后
```

---

## 📊 方案对比

| 特性 | HTTPS | SSH |
|------|-------|-----|
| 配置复杂度 | ⭐ 简单 | ⭐⭐⭐ 中等 |
| 安全性 | ⭐⭐⭐ 高（Token） | ⭐⭐⭐⭐ 高（密钥） |
| 便利性 | 每次换账号要输密码 | 配置后自动切换 |
| 适合场景 | 偶尔推送 | 频繁推送/多账号 |
| 密钥管理 | Git Credential | ~/.ssh/config |

---

## 🎉 推荐方案

**对于你当前的情况**：

✅ **短期快速**：保持 HTTPS，设置凭据助手
```bash
git config --global credential.helper osxkeychain
# 然后 git push，输入 Personal Access Token
```

✅ **长期生产**：配置 SSH 多账号（5分钟）
```bash
bash .generate-humditty-key.sh
# 添加公钥到 GitHub
git remote set-url origin github-humditty:humditty/claude-memory-system.git
ssh -T git@github-humditty  # 测试
```

---

## 📝 总结清单

- [ ] 决定使用 HTTPS 还是 SSH
- [ ] 如果 HTTPS：创建 Personal Access Token
- [ ] 如果 SSH：运行 `.generate-humditty-key.sh`
- [ ] 将公钥添加到 GitHub humditty 账号
- [ ] 更新或创建 `~/.ssh/config`
- [ ] 切换项目 remote URL（如果使用 SSH）
- [ ] 测试 `git push` 和 `ssh -T`

---

**你的项目现在已经成功推送到 GitHub！** 🎉

只需要配置认证方式，以后就可以正常推送了。

---

**有任何问题？**
- 运行 `ssh -T git@github-humditty` 测试
- 查看 `git remote -v` 确认 URL
- 参考上面的"故障排除"章节
