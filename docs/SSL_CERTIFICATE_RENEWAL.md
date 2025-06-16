# SSL Certificate Renewal Guide

This document explains how to diagnose and fix SSL certificate issues for the great-reads.com website.

## What is an SSL Certificate?

SSL (Secure Sockets Layer) certificates are digital certificates that:
- Encrypt data between your website and visitors
- Verify your website's identity
- Enable HTTPS (the secure version of HTTP)
- Show the padlock icon in browsers

## Why Do SSL Certificates Expire?

SSL certificates have expiration dates for security reasons:
- **Security**: Limits the time a compromised certificate can be misused
- **Key rotation**: Forces regular updates to encryption keys
- **Validation**: Ensures domain ownership is regularly verified
- **Standard practice**: Industry standard is 90 days for Let's Encrypt certificates

## Common SSL Certificate Errors

When an SSL certificate expires or has issues, users will see errors like:

```
Your connection is not private
net::ERR_CERT_DATE_INVALID
```

This means:
- The certificate's validity period doesn't include the current date
- Browsers block access to protect users from potential security risks
- The website becomes inaccessible via HTTPS

## Our SSL Setup

The great-reads.com website uses:
- **Let's Encrypt**: Free SSL certificate provider
- **Nginx**: Web server that handles SSL termination
- **Certbot**: Tool for managing Let's Encrypt certificates
- **Automatic renewal**: Systemd timer that runs twice daily

### Certificate Location
```
Certificate: /etc/letsencrypt/live/great-reads.com/fullchain.pem
Private Key: /etc/letsencrypt/live/great-reads.com/privkey.pem
```

## Diagnosing SSL Certificate Issues

### 1. Check Certificate Status
```bash
sudo certbot certificates
```

This shows:
- Certificate name and domains
- Expiration date
- Validity status (VALID/EXPIRED/INVALID)
- File paths

### 2. Check Browser Error
Look for specific error codes:
- `ERR_CERT_DATE_INVALID`: Certificate expired or has wrong date
- `ERR_CERT_AUTHORITY_INVALID`: Certificate not from trusted authority
- `ERR_CERT_COMMON_NAME_INVALID`: Domain name mismatch

### 3. Test HTTPS Connection
```bash
curl -I https://great-reads.com
```

Successful response shows:
- HTTP/2 status (indicates SSL working)
- Security headers
- No certificate errors

## Renewing SSL Certificates

### Method 1: Automatic Renewal (Preferred)
Let's Encrypt certificates should renew automatically via systemd timer:

```bash
# Check if auto-renewal is enabled
sudo systemctl status certbot.timer

# Test renewal (dry run)
sudo certbot renew --dry-run
```

### Method 2: Manual Renewal
If automatic renewal fails or you need immediate renewal:

```bash
# Renew all certificates
sudo certbot renew --nginx

# Force renewal (even if not due)
sudo certbot renew --nginx --force-renewal

# Renew specific certificate
sudo certbot renew --nginx --cert-name great-reads.com
```

**Important**: Use `--nginx` flag to avoid stopping the web server during renewal.

### Method 3: Emergency Renewal
If the nginx method fails:

```bash
# Stop nginx temporarily
sudo systemctl stop nginx

# Renew certificate
sudo certbot renew --force-renewal

# Start nginx
sudo systemctl start nginx
```

## Post-Renewal Steps

After renewing certificates:

1. **Reload Nginx** (usually automatic with `--nginx` flag):
   ```bash
   sudo systemctl reload nginx
   ```

2. **Verify renewal**:
   ```bash
   sudo certbot certificates
   ```

3. **Test website**:
   ```bash
   curl -I https://great-reads.com
   ```

4. **Check browser access**: Visit https://great-reads.com

## Troubleshooting Common Issues

### Port 80 Already in Use
```
Could not bind TCP port 80 because it is already in use
```

**Solution**: Use the nginx plugin instead of standalone mode:
```bash
sudo certbot renew --nginx --force-renewal
```

### Domain Not Reachable
```
Domain great-reads.com is not reachable
```

**Causes**:
- DNS issues
- Firewall blocking traffic
- Nginx not running

**Solutions**:
```bash
# Check DNS
nslookup great-reads.com

# Check firewall
sudo ufw status

# Check nginx
sudo systemctl status nginx
```

### Certificate Authority Issues
If Let's Encrypt is having issues, check:
- [Let's Encrypt Status Page](https://letsencrypt.status.io/)
- Rate limits (5 certificates per domain per week)

## Monitoring and Maintenance

### Check Auto-Renewal Status
```bash
# Check timer status
sudo systemctl status certbot.timer

# View recent renewal attempts
sudo journalctl -u certbot.service --since "1 week ago"
```

### Set Up Monitoring
Add to your monitoring script:
```bash
# Check certificate expiration
sudo certbot certificates | grep "Expiry Date"

# Test renewal
sudo certbot renew --dry-run
```

### Certificate Expiration Alerts
Consider setting up email alerts for certificate expiration:
```bash
# Add to crontab
0 0 * * 0 /usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"
```

## Security Best Practices

1. **Keep certbot updated**:
   ```bash
   sudo apt update && sudo apt upgrade certbot
   ```

2. **Monitor certificate validity**:
   - Certificates expire every 90 days
   - Auto-renewal attempts happen twice daily
   - Manual check monthly

3. **Backup certificates** (optional):
   ```bash
   sudo cp -r /etc/letsencrypt/ /backup/letsencrypt-$(date +%Y%m%d)
   ```

4. **Security headers**: Ensure nginx config includes:
   ```nginx
   add_header Strict-Transport-Security "max-age=31536000" always;
   add_header X-Frame-Options "SAMEORIGIN";
   add_header X-XSS-Protection "1; mode=block";
   add_header X-Content-Type-Options "nosniff";
   ```

## Quick Reference Commands

```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew --nginx

# Force renewal
sudo certbot renew --nginx --force-renewal

# Test renewal
sudo certbot renew --dry-run

# Check auto-renewal timer
sudo systemctl status certbot.timer

# Reload nginx after renewal
sudo systemctl reload nginx

# Test HTTPS
curl -I https://great-reads.com
```

## When to Seek Help

Contact your system administrator or hosting provider if:
- Multiple renewal attempts fail
- DNS issues persist
- Rate limits are exceeded
- Certificate authority is unreachable
- Nginx configuration errors occur

## Step-by-Step Renewal Process

Here's exactly what we did to fix the SSL certificate issue:

### 1. Identify the Problem
```bash
# User reported browser error: ERR_CERT_DATE_INVALID
# This indicates an expired or invalid SSL certificate
```

### 2. Check Certificate Status
```bash
sudo certbot certificates
```
**Output showed**: Certificate expired on 2025-05-30 (marked as INVALID: EXPIRED)

### 3. Attempt Standard Renewal
```bash
sudo certbot renew --force-renewal
```
**Failed with**: "Could not bind TCP port 80 because it is already in use"

### 4. Use Nginx Plugin
```bash
sudo certbot renew --nginx --force-renewal
```
**Success**: Certificate renewed without stopping web server

### 5. Verify Renewal
```bash
sudo certbot certificates
```
**Confirmed**: New certificate valid for 89 days (until 2025-09-07)

### 6. Test Website
```bash
curl -I https://great-reads.com
```
**Result**: HTTP/2 response with security headers - SSL working properly

## Automation and Prevention

### Automatic Renewal Setup
The system should automatically renew certificates, but verify it's working:

```bash
# Check if the timer is active
sudo systemctl status certbot.timer

# Expected output:
# Active: active (waiting)
# Trigger: [next run time]
```

### Manual Monitoring
Set up a monthly check:

```bash
#!/bin/bash
# Add to crontab: 0 9 1 * * /path/to/ssl-check.sh

echo "=== SSL Certificate Status ==="
sudo certbot certificates

echo "=== Testing Renewal ==="
sudo certbot renew --dry-run

echo "=== Website Test ==="
curl -I https://great-reads.com
```

### Emergency Procedures

If the website is down due to SSL issues:

1. **Immediate fix** (temporary):
   ```bash
   # Users can bypass by clicking "Advanced" -> "Proceed to site (unsafe)"
   # Only recommend this for trusted sites
   ```

2. **Quick renewal**:
   ```bash
   sudo certbot renew --nginx --force-renewal
   sudo systemctl reload nginx
   ```

3. **If nginx method fails**:
   ```bash
   sudo systemctl stop nginx
   sudo certbot renew --force-renewal
   sudo systemctl start nginx
   ```

## Understanding the Error Messages

### Browser Errors
- **ERR_CERT_DATE_INVALID**: Certificate expired or system clock wrong
- **ERR_CERT_AUTHORITY_INVALID**: Certificate not from trusted CA
- **ERR_CERT_COMMON_NAME_INVALID**: Domain name doesn't match certificate
- **ERR_SSL_PROTOCOL_ERROR**: SSL/TLS handshake failed

### Certbot Errors
- **Port 80 in use**: Web server running, use `--nginx` flag
- **Rate limit exceeded**: Too many requests to Let's Encrypt (wait 1 week)
- **Domain validation failed**: DNS issues or firewall blocking
- **Challenge failed**: Let's Encrypt can't verify domain ownership

## Best Practices Summary

1. **Monitor regularly**: Check certificate status monthly
2. **Test renewals**: Run dry-run tests quarterly
3. **Keep logs**: Monitor certbot service logs
4. **Have backups**: Know how to restore from backup
5. **Document changes**: Keep track of configuration modifications
6. **Stay updated**: Keep certbot and nginx updated

## Troubleshooting Checklist

When SSL issues occur, check:

- [ ] Certificate expiration date
- [ ] DNS resolution working
- [ ] Nginx running and configured correctly
- [ ] Firewall allowing ports 80 and 443
- [ ] Let's Encrypt service status
- [ ] System clock accuracy
- [ ] Disk space available
- [ ] Rate limits not exceeded

## Related Documentation

- [NGINX Setup Guide](./NGINX_SETUP.md)
- [Server Setup Script](../scripts/server/setup_server.sh)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)

---

**Last Updated**: June 2025
**Next Review**: September 2025 (before certificate expiration)
