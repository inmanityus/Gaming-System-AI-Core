# End-User Testing Protocol

## Overview

When the user requests **"end user testing"**, **"test as an end user"**, **"manual testing"**, or similar phrases, follow this comprehensive protocol to emulate real human interaction with the application using frontend automation tools.

---

## 🎯 Purpose

**End-User Testing simulates REAL human usage of the application to:**
- Catch UI/UX issues that automated tests miss
- Verify complete logical flows work end-to-end
- Ensure proper page rendering and navigation
- Validate email content and formatting
- Confirm forms work correctly with real data
- Test authentication and authorization flows
- Verify error handling and user feedback

**This is NOT a replacement for automated test suites** - it's a complementary manual validation layer.

---

## 🛠️ Tools by Platform

### **Web Applications:**
- **Primary Tool:** Playwright (`mcp_Playwright_*` tools)
- **Email Testing:** MailHog (accessible via Playwright at `http://localhost:8025`)
- **Database Verification:** Direct PostgreSQL queries for data validation

### **Mobile Applications (Cross-Platform):**
- **Primary Tool:** Android Emulator MCP (project-specific)
- **Email Testing:** MailHog or similar (accessible via emulator browser)
- **Database Verification:** Direct database queries

### **Desktop Applications:**
- **Primary Tool:** Project-specific automation MCP
- **Email Testing:** MailHog or similar
- **Database Verification:** Direct database queries

**The protocol generalizes across all tools - adapt commands as needed.**

---

## 📋 The End-User Testing Workflow

### **Stage 1: Pre-Test Setup**

**1.1 Verify Services Running**
```bash
# Check web server
curl http://localhost:3000

# Check API server
curl http://localhost:4000/health

# Check MailHog
curl http://localhost:8025

# Check database
psql -h localhost -U postgres -d {database_name} -c "SELECT 1"
```

**1.2 Prepare Test Environment**
- Ensure test data exists in database
- Clear previous test artifacts
- Verify no users are actively using the system
- Note current database state for later rollback

**1.3 Create Screenshot Directory**
```bash
mkdir -p .logs/end-user-testing/{timestamp}/
```

**1.4 Document Testing Scope**
- What section are we testing? (e.g., "Admin Dashboard")
- What flows should be tested? (e.g., "User management flow")
- What data should be used? (e.g., "test@example.com")
- Expected outcomes?

---

### **Stage 2: Navigation & Access**

**2.1 Launch Frontend Tool**

For Playwright:
```typescript
// Navigate to starting URL
mcp_Playwright_browser_navigate({ url: "http://localhost:3000" })

// Take initial screenshot
mcp_Playwright_browser_take_screenshot({
  filename: "01-homepage.png",
  fullPage: true
})
```

**2.2 Authentication Flow (if required)**

**Example: Email + Passcode Login**

```typescript
// 1. Navigate to login
mcp_Playwright_browser_navigate({ url: "http://localhost:3000/admin/login" })
mcp_Playwright_browser_take_screenshot({ filename: "02-login-page.png" })

// 2. Enter email
mcp_Playwright_browser_type({
  element: "email input field",
  ref: "[ref from snapshot]",
  text: "admin@example.com",
  submit: false
})

// 3. Click "Send Code" button
mcp_Playwright_browser_click({
  element: "send code button",
  ref: "[ref from snapshot]"
})

// 4. Wait for email
await wait(3000)

// 5. Get passcode from database or MailHog
const passcode = await getPasscodeFromDatabase("admin@example.com")
// OR navigate to MailHog and extract passcode

// 6. Enter passcode
mcp_Playwright_browser_type({
  element: "passcode input",
  ref: "[ref from snapshot]",
  text: passcode,
  submit: false
})

// 7. Click verify button
mcp_Playwright_browser_click({
  element: "verify button",
  ref: "[ref from snapshot]"
})

// 8. Verify redirect to dashboard
await wait(2000)
mcp_Playwright_browser_take_screenshot({ filename: "03-dashboard-after-login.png" })

// 9. Verify we're on the correct page
const snapshot = await mcp_Playwright_browser_snapshot()
// Check snapshot contains expected dashboard elements
```

**2.3 Verify Successful Access**
- Screenshot shows expected page
- Navigation menu is correct for the section
- User information displayed correctly
- No error messages

---

### **Stage 3: Comprehensive Page Testing**

**3.1 Main Page Verification**

```typescript
// Take full page screenshot
mcp_Playwright_browser_take_screenshot({
  filename: "main-page.png",
  fullPage: true
})

// Verify page components:
const snapshot = await mcp_Playwright_browser_snapshot()
// Check:
// - Header loaded
// - Navigation menu present and correct
// - Content area loaded
// - Footer present
// - No loading spinners stuck
// - No error messages
// - Data displayed correctly
```

**3.2 Menu Testing - Click EVERY Menu Item**

```typescript
const menuItems = [
  { name: "Dashboard", url: "/admin/dashboard" },
  { name: "Users", url: "/admin/users" },
  { name: "Settings", url: "/admin/settings" },
  // ... etc
]

for (const item of menuItems) {
  // Click menu item
  mcp_Playwright_browser_click({
    element: `${item.name} menu link`,
    ref: "[ref from snapshot]"
  })
  
  // Wait for page load
  await wait(2000)
  
  // Screenshot
  mcp_Playwright_browser_take_screenshot({
    filename: `menu-${item.name.toLowerCase()}.png`,
    fullPage: true
  })
  
  // Verify page loaded correctly
  const snapshot = await mcp_Playwright_browser_snapshot()
  // - Check URL matches expected
  // - Check page title correct
  // - Check content loaded
  // - Check no errors
  
  // Verify screenshot shows proper page
  // (AI reviews screenshot)
  
  // Delete screenshot if passed
  deleteScreenshot(`menu-${item.name.toLowerCase()}.png`)
}
```

**3.3 Link Testing - Click EVERY Link on EVERY Page**

```typescript
// For each page, get all links
const snapshot = await mcp_Playwright_browser_snapshot()
// Extract all clickable links from snapshot

for (const link of allLinks) {
  // Click link
  mcp_Playwright_browser_click({
    element: `${link.text} link`,
    ref: link.ref
  })
  
  // Wait for navigation/modal/action
  await wait(1500)
  
  // Screenshot result
  mcp_Playwright_browser_take_screenshot({
    filename: `link-${link.id}.png`
  })
  
  // Verify:
  // - Correct page/modal/action occurred
  // - Content is correct
  // - No errors
  
  // Navigate back if needed
  if (navigatedAway) {
    mcp_Playwright_browser_navigate_back()
  }
  
  // Delete screenshot if passed
  deleteScreenshot(`link-${link.id}.png`)
}
```

---

### **Stage 4: Form Testing**

**4.1 Form Loading & Prefill Validation**

```typescript
// Navigate to form page
mcp_Playwright_browser_navigate({ url: "/admin/users/123/edit" })

// Screenshot form
mcp_Playwright_browser_take_screenshot({
  filename: "form-loaded.png",
  fullPage: true
})

// If form should be prefilled:
// 1. Get expected data from database
const dbData = await query(`
  SELECT name, email, bio 
  FROM users 
  WHERE id = 123
`)

// 2. Extract form values from snapshot
const formSnapshot = await mcp_Playwright_browser_snapshot()
// Parse form field values from snapshot

// 3. Compare database data with form prefill
if (dbData.name !== formData.name) {
  reportIssue("Form prefill mismatch: name field")
}
if (dbData.email !== formData.email) {
  reportIssue("Form prefill mismatch: email field")
}
// ... validate all fields

// 4. Verify form validation rules work
// Try submitting invalid data, ensure errors shown
```

**4.2 Form Submission & Validation**

```typescript
// Fill out form
mcp_Playwright_browser_fill_form({
  fields: [
    { name: "Name", type: "textbox", ref: "[ref]", value: "John Doe" },
    { name: "Email", type: "textbox", ref: "[ref]", value: "john@example.com" },
    { name: "Active", type: "checkbox", ref: "[ref]", value: "true" }
  ]
})

// Screenshot before submit
mcp_Playwright_browser_take_screenshot({
  filename: "form-filled.png"
})

// Submit form
mcp_Playwright_browser_click({
  element: "submit button",
  ref: "[ref]"
})

// Wait for response
await wait(2000)

// Screenshot result
mcp_Playwright_browser_take_screenshot({
  filename: "form-submitted.png"
})

// Verify one of:
// - Success message displayed
// - Redirected to confirmation page
// - Item appears in list
// - Email sent (check MailHog)

// Verify database updated correctly
const updated = await query(`
  SELECT name, email 
  FROM users 
  WHERE email = 'john@example.com'
`)
if (updated.name !== "John Doe") {
  reportIssue("Database not updated correctly")
}
```

---

### **Stage 5: Email Testing**

**5.1 Check Email Was Sent**

```typescript
// Navigate to MailHog
mcp_Playwright_browser_navigate({ url: "http://localhost:8025" })

// Screenshot inbox
mcp_Playwright_browser_take_screenshot({
  filename: "mailhog-inbox.png"
})

// Find the email (newest first)
const snapshot = await mcp_Playwright_browser_snapshot()
// Identify email in list

// Click on email
mcp_Playwright_browser_click({
  element: "email from test",
  ref: "[ref of email in list]"
})

// Screenshot email content
mcp_Playwright_browser_take_screenshot({
  filename: "email-content.png",
  fullPage: true
})
```

**5.2 Verify Email Content**

```typescript
// Get email HTML content from MailHog or snapshot
const emailSnapshot = await mcp_Playwright_browser_snapshot()

// Verify:
// - Subject line correct
// - Recipient correct
// - Sender correct
// - Body content correct
// - Formatting looks good (no broken HTML)
// - Images load correctly
// - Links present and correct
// - Call-to-action buttons work
// - Personalization correct (user name, etc.)

// Check specific content elements
if (!emailContent.includes("Welcome, John!")) {
  reportIssue("Email personalization missing")
}
if (!emailContent.includes("Click here to verify")) {
  reportIssue("Email missing verification link")
}
```

**5.3 Test Email Links**

```typescript
// Click link in email
mcp_Playwright_browser_click({
  element: "verify email button",
  ref: "[ref from email]"
})

// Should open website in new tab or same tab
await wait(2000)

// Screenshot destination page
mcp_Playwright_browser_take_screenshot({
  filename: "email-link-destination.png"
})

// Verify:
// - Correct page loaded
// - Page shows success message or appropriate content
// - User is logged in if applicable
// - Action was completed (database check)

const verified = await query(`
  SELECT email_verified 
  FROM users 
  WHERE email = 'john@example.com'
`)
if (!verified.email_verified) {
  reportIssue("Email verification link didn't work")
}
```

---

### **Stage 6: Complete Logical Flow Testing**

**6.1 Define Flow Steps**

Example: "User Registration Flow"
1. Visit homepage
2. Click "Sign Up"
3. Fill registration form
4. Submit form
5. Check email for verification link
6. Click verification link
7. Redirected to welcome page
8. Log in
9. See dashboard

**6.2 Execute Each Step**

```typescript
// Step 1: Homepage
mcp_Playwright_browser_navigate({ url: "http://localhost:3000" })
mcp_Playwright_browser_take_screenshot({ filename: "flow-01-homepage.png" })
verifyPageLoaded("Homepage")

// Step 2: Click Sign Up
mcp_Playwright_browser_click({ element: "Sign Up button", ref: "[ref]" })
await wait(1500)
mcp_Playwright_browser_take_screenshot({ filename: "flow-02-signup-page.png" })
verifyPageLoaded("Sign Up Page")

// Step 3: Fill Form
mcp_Playwright_browser_fill_form({
  fields: [
    { name: "Email", type: "textbox", ref: "[ref]", value: "newuser@example.com" },
    { name: "Name", type: "textbox", ref: "[ref]", value: "New User" },
    { name: "Password", type: "textbox", ref: "[ref]", value: "SecurePass123!" }
  ]
})
mcp_Playwright_browser_take_screenshot({ filename: "flow-03-form-filled.png" })

// Step 4: Submit
mcp_Playwright_browser_click({ element: "Create Account button", ref: "[ref]" })
await wait(2000)
mcp_Playwright_browser_take_screenshot({ filename: "flow-04-after-submit.png" })
verifyMessage("Check your email for verification link")

// Step 5: Check Email
mcp_Playwright_browser_navigate({ url: "http://localhost:8025" })
// ... find and open verification email
mcp_Playwright_browser_take_screenshot({ filename: "flow-05-verification-email.png" })

// Step 6: Click Link
// ... click verification link in email
mcp_Playwright_browser_take_screenshot({ filename: "flow-06-after-verify.png" })

// Step 7: Welcome Page
verifyPageLoaded("Welcome Page")

// Step 8: Login
// ... perform login
mcp_Playwright_browser_take_screenshot({ filename: "flow-07-logged-in.png" })

// Step 9: Dashboard
verifyPageLoaded("User Dashboard")
mcp_Playwright_browser_take_screenshot({ filename: "flow-08-dashboard.png" })

// Verify complete flow in database
const user = await query(`
  SELECT id, email, email_verified, created_at 
  FROM users 
  WHERE email = 'newuser@example.com'
`)
if (!user.email_verified) {
  reportIssue("User registration flow failed - email not verified")
}
```

**6.3 Verify at Each Step**
- Page loads correctly (no errors)
- Content displays as expected
- User sees appropriate feedback
- Database state is correct
- Emails sent at right time with correct content

---

### **Stage 7: Error Handling & Edge Cases**

**7.1 Test Error Conditions**

```typescript
// Example: Invalid form submission
mcp_Playwright_browser_fill_form({
  fields: [
    { name: "Email", type: "textbox", ref: "[ref]", value: "invalid-email" },
  ]
})
mcp_Playwright_browser_click({ element: "submit button", ref: "[ref]" })

// Verify error message shown
await wait(1000)
mcp_Playwright_browser_take_screenshot({ filename: "error-invalid-email.png" })

const snapshot = await mcp_Playwright_browser_snapshot()
if (!snapshot.includes("Invalid email format")) {
  reportIssue("Missing error message for invalid email")
}
```

**7.2 Test Authorization**

```typescript
// Try accessing admin page as regular user
// Should be denied or redirected

// Try accessing another user's data
// Should get 403 Forbidden

// Try accessing without authentication
// Should redirect to login
```

---

### **Stage 8: Issue Discovery & Resolution**

**8.1 When Issue Found**

```typescript
function reportIssue(description: string, severity: "Critical"|"High"|"Medium"|"Low") {
  // Log issue
  logIssue({
    description,
    severity,
    screenshot: currentScreenshot,
    url: currentUrl,
    timestamp: new Date()
  })
  
  // Keep screenshot for this issue (don't delete)
  // Mark for investigation
}
```

**8.2 Fix Issues Immediately**

When an issue is discovered:
1. **Stop current testing**
2. **Document the issue** with screenshot
3. **Analyze the problem** (frontend? backend? database?)
4. **Fix the code** using peer-based coding protocol
5. **Restart testing from beginning** of affected flow
6. **Verify fix works**
7. **Continue testing**

**8.3 Issue Categories**

- **Critical:** Prevents core functionality, security issue, data loss
- **High:** Major feature broken, poor UX, missing critical content
- **Medium:** Minor feature issue, cosmetic problem, unclear messaging
- **Low:** Typo, minor visual inconsistency, nice-to-have missing

---

### **Stage 9: Post-Test Cleanup**

**9.1 Database Rollback**

```sql
-- Rollback test data changes
DELETE FROM users WHERE email LIKE '%@example.com%';
DELETE FROM test_submissions WHERE created_at > '{test_start_time}';
-- Restore any modified records
UPDATE users SET name = '{original_name}' WHERE id = 123;
```

**9.2 Delete Screenshots**

```bash
# Delete all screenshots unless told otherwise
rm -rf .logs/end-user-testing/{timestamp}/

# OR selectively delete passed screenshots
# Keep only screenshots showing issues
```

**9.3 Close Browser**

```typescript
mcp_Playwright_browser_close()
```

**9.4 Generate Test Report**

```markdown
# End-User Test Report
Date: 2025-10-10
Section: Admin Dashboard
Tester: AI End-User Testing Protocol

## Summary
- Pages tested: 15
- Links tested: 47
- Forms tested: 8
- Emails tested: 5
- Logical flows tested: 3

## Issues Found
### Critical (0)
None

### High (2)
1. User edit form doesn't validate email format
2. Delete confirmation modal doesn't close on cancel

### Medium (3)
1. Dashboard chart labels truncated
2. Email template missing footer
3. Search results don't show user status

### Low (1)
1. Typo in success message: "Sucessfully" → "Successfully"

## Issues Fixed
All Critical and High issues fixed and re-tested.

## Test Coverage
✅ Navigation menu - all links work
✅ User management - CRUD operations
✅ Form validation - all tested
✅ Email flows - verified content and links
✅ Authentication - login/logout flows

## Recommendations
- Add loading spinner for search
- Improve error messages on user form
- Add confirmation for bulk actions
```

---

## 🎯 Testing Checklist

### **For Every Page:**
- [ ] Page loads without errors
- [ ] Page title correct
- [ ] Navigation menu correct
- [ ] Content displays properly
- [ ] Images load
- [ ] No console errors (check browser logs)
- [ ] Responsive layout works
- [ ] Screenshot taken and verified
- [ ] Screenshot deleted after passing

### **For Every Menu Item:**
- [ ] Clicks successfully
- [ ] Navigates to correct page
- [ ] Page loads completely
- [ ] Correct permissions enforced

### **For Every Link:**
- [ ] Clicks successfully
- [ ] Opens correct destination
- [ ] Target loads properly
- [ ] Back button works (if applicable)

### **For Every Form:**
- [ ] Loads with correct fields
- [ ] Prefilled data matches database
- [ ] Validation works (try invalid data)
- [ ] Submission succeeds
- [ ] Success/error messages shown
- [ ] Database updated correctly
- [ ] Emails sent (if applicable)
- [ ] User redirected or shown confirmation

### **For Every Email:**
- [ ] Email received in MailHog
- [ ] Subject correct
- [ ] Recipient correct
- [ ] Content correct
- [ ] Formatting looks good
- [ ] Personalization correct
- [ ] Links work
- [ ] Call-to-action buttons work

### **For Every Logical Flow:**
- [ ] All steps complete successfully
- [ ] User sees appropriate feedback at each step
- [ ] Emails sent at right times
- [ ] Database state correct at each step
- [ ] Error handling works
- [ ] Final state correct

---

## 🚫 Common Mistakes to Avoid

**Don't:**
- ❌ Rely solely on automated test suites
- ❌ Skip screenshots
- ❌ Test only the "happy path"
- ❌ Ignore error conditions
- ❌ Forget to check emails
- ❌ Leave test data in database
- ❌ Keep screenshots after testing
- ❌ Rush through flows
- ❌ Miss edge cases

**Do:**
- ✅ Test as a real user would
- ✅ Click every link and button
- ✅ Try invalid inputs
- ✅ Verify all emails
- ✅ Check database state
- ✅ Screenshot everything
- ✅ Clean up after testing
- ✅ Fix issues immediately
- ✅ Retest after fixes

---

## 📊 Success Criteria

**Testing is complete when:**
1. ✅ All pages load correctly
2. ✅ All navigation works
3. ✅ All links function
4. ✅ All forms submit correctly
5. ✅ All emails send with correct content
6. ✅ All logical flows complete successfully
7. ✅ All issues found are fixed
8. ✅ User would have perfect experience
9. ✅ Database is clean
10. ✅ Screenshots are deleted

**Goal:** User should NEVER find an issue that testing missed.

---

## 🔄 Tool-Specific Commands

### **Playwright (Web)**

```typescript
// Navigation
mcp_Playwright_browser_navigate({ url })
mcp_Playwright_browser_navigate_back()

// Interaction
mcp_Playwright_browser_click({ element, ref })
mcp_Playwright_browser_type({ element, ref, text, submit })
mcp_Playwright_browser_fill_form({ fields })
mcp_Playwright_browser_select_option({ element, ref, values })
mcp_Playwright_browser_drag({ startElement, startRef, endElement, endRef })

// Inspection
mcp_Playwright_browser_snapshot()
mcp_Playwright_browser_take_screenshot({ filename, fullPage })
mcp_Playwright_browser_console_messages({ onlyErrors })
mcp_Playwright_browser_network_requests()

// Wait
mcp_Playwright_browser_wait_for({ time, text, textGone })

// Tabs
mcp_Playwright_browser_tabs({ action: "list"|"new"|"close"|"select", index })

// Cleanup
mcp_Playwright_browser_close()
```

### **Android Emulator MCP (Mobile)**
*(Commands will be project-specific - adapt as needed)*

```typescript
// Similar pattern but emulator-specific
emulator_navigate({ screen })
emulator_tap({ element })
emulator_swipe({ direction })
emulator_input({ field, text })
emulator_screenshot({ filename })
// etc.
```

---

## 🐧 Setup for Linux Cursor

1. **Copy Documentation**
   ```bash
   cp docs/End-User-Testing.md /path/to/linux/project/
   ```

2. **Install Playwright**
   ```bash
   npm install -D @playwright/test
   npx playwright install chromium
   ```

3. **Configure MailHog**
   ```bash
   # Install MailHog
   brew install mailhog  # or appropriate package manager
   
   # Run MailHog
   mailhog
   # Access at http://localhost:8025
   ```

4. **Add to Startup Script**
   ```bash
   # Verify Playwright MCP configured
   # Verify MailHog running
   # Create .logs/end-user-testing/ directory
   ```

5. **Test Setup**
   ```bash
   # Run sample end-user test to verify configuration
   ```

---

## 📚 Related Documentation

- [Playwright MCP Documentation](https://github.com/executeautomation/mcp-playwright)
- [MailHog Documentation](https://github.com/mailhog/MailHog)
- [Peer-Based Coding Protocol](./Peer-Coding.md)
- [Security Baseline](./Security-Baseline.md)

---

## 🔄 Version History

- **v1.0** - Initial end-user testing protocol
- Created: 2025-10-10
- Last Updated: 2025-10-10

---

**End-User Testing ensures the application works flawlessly from a real user's perspective, catching issues that automated tests miss and validating complete user experiences.**





