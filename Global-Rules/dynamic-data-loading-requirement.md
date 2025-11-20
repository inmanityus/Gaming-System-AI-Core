# Dynamic Data Loading Requirement - Global Rule

**Status**: ✅ **MANDATORY**  
**Date**: 2025-10-27  
**Impact**: ALL Frontend Applications  
**Severity**: Critical

---

## 🚨 CRITICAL RULE

### MANDATORY REQUIREMENT

**If a page or component needs to load data or configuration from a backend app or data source, it MUST be built dynamically - NOT statically.**

Static pages are ONLY acceptable for:
- Pure content pages (about, contact, marketing pages with no user-specific data)
- Public landing pages with no personalized content
- Public documentation or help pages

---

## ❌ PROHIBITED PATTERNS

### Anti-Pattern: Static Page per User

**NEVER DO THIS:**

```javascript
// ❌ WRONG: Generating static pages for every user
export async function generateStaticParams() {
  const users = await fetchAllUsers(); // Get all users from database
  return users.map(user => ({ id: user.id }));
}

export default function UserPage({ params }) {
  // This creates a static page for EVERY user
  // Server must regenerate ALL pages when any user changes
}
```

**Problems:**
1. **Scalability**: Breaks at scale (10,000 users = 10,000 static pages to generate)
2. **Data Freshness**: Static pages don't reflect real-time data changes
3. **Build Time**: Generating thousands of pages during build takes hours/days
4. **Resource Waste**: Unnecessary disk space and build resources
5. **Maintenance Overhead**: Any user change requires full rebuild

### Anti-Pattern: Static Component with Backend Data

**NEVER DO THIS:**

```javascript
// ❌ WRONG: Static component fetching data at build time
export async function generateStaticProps() {
  const data = await fetch('/api/dynamic-data'); // Backend data
  return { props: { data } }; // Used at BUILD time only
}

export default function DynamicComponent({ data }) {
  // Data is stale immediately after build
  // Any change requires full rebuild
}
```

**Problems:**
1. **Stale Data**: Data is only as fresh as the last build
2. **Not Dynamic**: Updates require full application rebuild
3. **User-Specific Data**: Can't show personalized content
4. **Real-Time Updates**: Impossible without rebuild

---

## ✅ CORRECT IMPLEMENTATIONS

### Pattern 1: Server-Side Rendering (SSR)

**Use This Instead:**

```javascript
// ✅ CORRECT: Dynamic Server-Side Rendering
// Next.js example with dynamic rendering
export const dynamic = 'force-dynamic'; // Force dynamic rendering
export const revalidate = 0; // No caching

export default async function UserPage({ params }) {
  const user = await fetch(`/api/users/${params.id}`); // Fresh data on request
  const posts = await fetch(`/api/users/${params.id}/posts`); // Fresh data
  
  return (
    <div>
      <h1>{user.name}</h1>
      <Posts data={posts} />
    </div>
  );
}
```

**Benefits:**
- ✅ Fresh data on every request
- ✅ Real-time updates
- ✅ User-specific content
- ✅ Scales to any number of users

### Pattern 2: Client-Side Fetching

**Use This Instead:**

```javascript
// ✅ CORRECT: Client-side data fetching
'use client'; // Client component (Next.js 13+)

export default function UserComponent() {
  const { data, isLoading, error } = useSWR('/api/user-data', fetcher);
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage />;
  
  return <UserDataDisplay data={data} />;
}
```

**Benefits:**
- ✅ Real-time data updates
- ✅ Automatic revalidation
- ✅ User-specific content
- ✅ No build required for updates

### Pattern 3: Hybrid Approach (Static + Dynamic)

**Use This Instead:**

```javascript
// ✅ CORRECT: Static shell with dynamic content
// Static shell loads instantly, dynamic content loads after
export async function generateStaticProps() {
  return {
    props: {
      // Static content that doesn't change frequently
      staticData: {
        layout: 'default',
        theme: 'light'
      }
    }
  };
}

export default function HybridPage({ staticData }) {
  // Static shell renders immediately
  return (
    <Layout {...staticData}>
      {/* Dynamic component loads data client-side */}
      <DynamicUserContent />
    </Layout>
  );
}
```

**Benefits:**
- ✅ Fast initial page load
- ✅ Fresh dynamic content
- ✅ Best of both worlds

---

## 📋 Decision Matrix

### When to Use Static Generation

| Content Type | Static? | Rationale |
|--------------|---------|-----------|
| Marketing pages | ✅ Yes | No backend data, public content |
| Documentation | ✅ Yes | Public content, rarely changes |
| Blog posts (markdown) | ✅ Yes | Static content at build time |
| User dashboards | ❌ No | Per-user data, must be dynamic |
| User profiles | ❌ No | Per-user data, must be dynamic |
| E-commerce product pages | ⚠️ Hybrid | Static structure + dynamic inventory |
| Admin panels | ❌ No | User-specific data, must be dynamic |
| Search results | ❌ No | Dynamic queries, must be dynamic |
| Personalized feeds | ❌ No | User-specific, real-time data |
| Chat/real-time | ❌ No | Real-time data, must be dynamic |

### When to Use Dynamic Rendering

| Use Case | Must Be Dynamic | Why |
|----------|----------------|-----|
| User authentication required | ✅ Yes | User-specific content |
| Data from database | ✅ Yes | Fresh data needed |
| Real-time updates | ✅ Yes | Live data changes |
| User-specific content | ✅ Yes | Personalized experience |
| Configuration from backend | ✅ Yes | Dynamic configuration |
| A/B testing | ✅ Yes | Dynamic experiments |
| Personalization | ✅ Yes | Per-user customization |
| Forms with backend validation | ✅ Yes | Server-side validation |

---

## 🔧 Implementation Guidelines

### For Next.js Applications

#### ❌ DON'T: Force Static Generation for Dynamic Content

```javascript
// ❌ WRONG: Forcing static generation for user pages
export async function generateStaticParams() {
  return [{ id: '1' }, { id: '2' }]; // Only 2 static pages
}

export const revalidate = 3600; // Static for 1 hour
```

#### ✅ DO: Use Dynamic Rendering

```javascript
// ✅ CORRECT: Dynamic rendering for user pages
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default async function Page({ params }) {
  const data = await fetchData(params.id);
  return <Content data={data} />;
}
```

### For React Applications

#### ❌ DON'T: Fetch Data at Component Import Time

```javascript
// ❌ WRONG: Data fetched at import time (static)
const data = await fetch('/api/data'); // Runs at module load

export default function Component() {
  return <Display data={data} />; // Stale data
}
```

#### ✅ DO: Fetch Data When Component Renders

```javascript
// ✅ CORRECT: Data fetched at render time (dynamic)
export default function Component() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch('/api/data')
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      });
  }, []);
  
  if (loading) return <Spinner />;
  return <Display data={data} />;
}
```

### For Vue Applications

#### ❌ DON'T: Use Static Props for Dynamic Data

```javascript
// ❌ WRONG: Static props for dynamic data
export default {
  async asyncData() {
    const data = await fetch('/api/data'); // Static at build
    return { data };
  }
};
```

#### ✅ DO: Fetch Data in Created/Mounted Hook

```javascript
// ✅ CORRECT: Dynamic data fetching
export default {
  data() {
    return { data: null, loading: true };
  },
  async created() {
    this.data = await fetch('/api/data'); // Fresh on every request
    this.loading = false;
  }
};
```

### For Angular Applications

#### ❌ DON'T: Use Static Configuration for Dynamic Data

```typescript
// ❌ WRONG: Static configuration with dynamic data
@Component({
  selector: 'app-component',
  templateUrl: './component.html'
})
export class Component {
  data = STATIC_DATA; // Never updates
}
```

#### ✅ DO: Use Services for Dynamic Data

```typescript
// ✅ CORRECT: Service for dynamic data
@Component({
  selector: 'app-component',
  templateUrl: './component.html'
})
export class Component implements OnInit {
  data$: Observable<any>;
  
  constructor(private dataService: DataService) {}
  
  ngOnInit() {
    this.data$ = this.dataService.getData(); // Fresh on load
  }
}
```

---

## 🎯 Real-World Examples

### Example 1: User Dashboard

```javascript
// ❌ WRONG: Static generation for user dashboard
export async function generateStaticParams() {
  const users = await getAllUsers(); // 10,000 users
  return users.map(user => ({ id: user.id }));
  // Generates 10,000 static pages - BREAKS AT SCALE
}

export const revalidate = 3600; // Data stale for 1 hour
```

```javascript
// ✅ CORRECT: Dynamic rendering for user dashboard
export const dynamic = 'force-dynamic';

export default async function Dashboard({ params }) {
  const user = await getUserData(params.userId); // Fresh on every request
  const tasks = await getUserTasks(params.userId); // Fresh data
  const notifications = await getNotifications(params.userId); // Real-time
  
  return (
    <DashboardLayout>
      <UserInfo user={user} />
      <TaskList tasks={tasks} />
      <NotificationPanel notifications={notifications} />
    </DashboardLayout>
  );
}
```

### Example 2: Search Results

```javascript
// ❌ WRONG: Static search results
export async function generateStaticProps({ params }) {
  const results = await search(params.query); // Static at build time
  return { props: { results } };
}
```

```javascript
// ✅ CORRECT: Dynamic search results
export const dynamic = 'force-dynamic';

export default async function SearchPage({ searchParams }) {
  const results = await search(searchParams.q); // Fresh on every query
  return <SearchResults results={results} />;
}
```

---

## 🚨 Detection and Prevention

### Code Review Checklist

When reviewing frontend code, ask:

1. ✅ Does this page load data from a backend?
   - If YES → Must be dynamic
   - If NO → Can be static

2. ✅ Is this data user-specific?
   - If YES → Must be dynamic
   - If NO → Consider hybrid approach

3. ✅ Does this data change frequently?
   - If YES → Must be dynamic
   - If NO → Might be static with revalidation

4. ✅ Does this require authentication?
   - If YES → Must be dynamic
   - If NO → Check other factors

5. ✅ Is this part of a real-time feature?
   - If YES → Must be dynamic
   - If NO → Check other factors

### Automated Detection

Add ESLint rules to detect problematic patterns:

```json
{
  "rules": {
    "no-static-generator-for-user-pages": "error",
    "require-dynamic-for-backend-data": "warn"
  }
}
```

### Pre-commit Hooks

Add validation to prevent anti-patterns:

```bash
# Check for static generation of user-specific pages
if grep -r "generateStaticParams" src/pages/users/; then
  echo "ERROR: Static generation for user pages detected!"
  echo "User pages MUST be dynamic"
  exit 1
fi
```

---

## 📚 Documentation References

- Next.js Dynamic Rendering: https://nextjs.org/docs/app/building-your-application/rendering/server-components#dynamic-rendering
- React Server Components: https://react.dev/reference/rsc
- Vue SSR: https://vuejs.org/guide/scaling-up/ssr.html
- Angular SSR: https://angular.io/guide/ssr

---

## ✅ Summary

**CRITICAL RULE**: If a page or component needs data from a backend, it MUST be dynamic.

**Static Pages** = Content that never changes  
**Dynamic Pages** = Content that changes or is user-specific

**Never generate static pages for:**
- User profiles
- Dashboards
- Search results
- Real-time data
- User-specific content
- Backend configuration

**Always use dynamic rendering for:**
- Any data from database
- Any user-specific content
- Any real-time features
- Any authenticated content

---

**This rule applies to ALL frontend frameworks and applications.**

**Last Updated**: 2025-10-27  
**Maintainer**: Development Team  
**Status**: ✅ **MANDATORY - DO NOT VIOLATE**







