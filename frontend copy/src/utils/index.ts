export function createPageUrl(page: string): string {
  // Simple routing utility - converts page names to URLs
  const baseUrl = '/';
  
  // Handle query parameters
  if (page.includes('?')) {
    const [pageName, queryString] = page.split('?');
    return `${baseUrl}${pageName.toLowerCase()}?${queryString}`;
  }
  
  return `${baseUrl}${page.toLowerCase()}`;
}

export function cn(...classes: (string | undefined | null | boolean)[]): string {
  return classes.filter(Boolean).join(' ');
}
