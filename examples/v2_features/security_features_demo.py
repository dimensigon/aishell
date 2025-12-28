"""
Advanced Security Features Demo

Demonstrates v2.0.0 security features including:
- Two-factor authentication (2FA/TOTP)
- SSO integration
- Certificate-based authentication
- Database activity monitoring
- Anomaly detection
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.security.advanced.advanced_auth import (
    TwoFactorAuth,
    SSOManager,
    CertificateAuth,
    AuthenticationMethod
)
from src.security.advanced.activity_monitor import (
    ActivityMonitor,
    AnomalyDetector,
    EventType,
    ThreatLevel
)


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_two_factor_auth():
    """Demo: Two-factor authentication"""
    print_section("1. Two-Factor Authentication (2FA)")

    twofa = TwoFactorAuth(issuer="AI-Shell-Demo")

    if not twofa.available:
        print("⚠️  pyotp not installed")
        print("   Install with: pip install pyotp")
        print("   Then run this demo again\n")
        return

    # Generate secret for user
    secret = twofa.generate_secret()
    print(f"Generated TOTP Secret: {secret}\n")

    # Get provisioning URI for QR code
    uri = twofa.get_provisioning_uri(
        secret,
        "user@example.com",
        "Demo User"
    )
    print(f"Provisioning URI (for QR code):\n{uri}\n")

    # Get current TOTP code
    current_code = twofa.get_current_code(secret)
    print(f"Current TOTP Code: {current_code}\n")

    # Verify code
    is_valid = twofa.verify_code(secret, current_code)
    print(f"✓ Code verified: {is_valid}\n")

    # Test invalid code
    is_valid = twofa.verify_code(secret, "000000")
    print(f"✗ Invalid code rejected: {not is_valid}\n")

    # Generate backup codes
    backup_codes = twofa.generate_backup_codes(10)
    print("Backup Codes (save securely):")
    for i, code in enumerate(backup_codes, 1):
        print(f"  {i:2d}. {code}")


def demo_sso_integration():
    """Demo: SSO integration"""
    print_section("2. Single Sign-On (SSO) Integration")

    sso = SSOManager()

    # Configure OAuth provider (e.g., Google)
    print("Configuring OAuth 2.0 provider (Google)...")
    sso.configure_oauth_provider(
        provider_name="google",
        client_id="demo-client-id",
        client_secret="demo-client-secret",
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
        scopes=["openid", "email", "profile"]
    )
    print("✓ Google OAuth configured\n")

    # Initiate OAuth flow
    if sso.oauth_available:
        print("Initiating OAuth login flow...")
        result = sso.initiate_oauth_login(
            "google",
            redirect_uri="https://example.com/callback",
            state="random-state-token"
        )
        if result:
            auth_url, state = result
            print(f"Authorization URL: {auth_url[:80]}...")
            print(f"State token: {state}\n")
    else:
        print("⚠️  requests-oauthlib not installed")
        print("   Install with: pip install requests-oauthlib\n")

    # Configure SAML provider (e.g., Okta)
    if sso.saml_available:
        print("Configuring SAML 2.0 provider (Okta)...")
        sso.configure_saml_provider(
            provider_name="okta",
            idp_entity_id="https://example.okta.com",
            idp_sso_url="https://example.okta.com/app/sso/saml",
            idp_x509_cert="DEMO_CERTIFICATE",
            sp_entity_id="https://aishell.example.com",
            sp_acs_url="https://aishell.example.com/saml/acs"
        )
        print("✓ Okta SAML configured\n")
    else:
        print("⚠️  python3-saml not installed")
        print("   Install with: pip install python3-saml\n")


def demo_certificate_auth():
    """Demo: Certificate-based authentication"""
    print_section("3. Certificate-Based Authentication")

    cert_auth = CertificateAuth()

    if not cert_auth.available:
        print("⚠️  cryptography library not available")
        print("   Install with: pip install cryptography\n")
        return

    print("Certificate authentication ready")
    print("Features:")
    print("  - X.509 client certificate validation")
    print("  - CA chain verification")
    print("  - Certificate pinning support")
    print("  - Revocation checking (CRL/OCSP)")
    print("\nNote: Requires actual certificates for demo")


def demo_activity_monitoring():
    """Demo: Database activity monitoring"""
    print_section("4. Database Activity Monitoring")

    monitor = ActivityMonitor(retention_days=90)

    print("Simulating database activity...\n")

    # Simulate various activities
    users = ["alice", "bob", "charlie"]

    for user in users:
        # Login event
        monitor.log_event(
            EventType.LOGIN,
            user,
            f"User {user} logged in",
            ip_address=f"192.168.1.{hash(user) % 255}",
            session_id=f"session_{user}"
        )

        # Query events
        queries = [
            ("SELECT * FROM users WHERE id = 1", 0.05, 1),
            ("SELECT * FROM orders WHERE user_id = 1", 0.12, 15),
            ("UPDATE users SET last_login = NOW() WHERE id = 1", 0.03, 1)
        ]

        for sql, exec_time, rows in queries:
            monitor.log_query(
                user,
                sql,
                exec_time,
                rows,
                success=True,
                ip_address=f"192.168.1.{hash(user) % 255}"
            )

    # Get statistics
    stats = monitor.get_statistics(time_window=timedelta(hours=1))

    print("Activity Statistics (last hour):")
    print(f"  Total events: {stats['total_events']}")
    print(f"  Unique users: {stats['unique_users']}")
    print(f"  Events by type:")
    for event_type, count in stats['events_by_type'].items():
        print(f"    {event_type}: {count}")
    print()

    # Get user activity summary
    print("User Activity Summary (alice):")
    summary = monitor.get_user_activity_summary("alice")
    print(f"  Total events: {summary['total_events']}")
    print(f"  Recent events (24h): {summary['recent_events_24h']}")


def demo_anomaly_detection():
    """Demo: Anomaly detection"""
    print_section("5. Anomaly Detection")

    monitor = ActivityMonitor()
    detector = AnomalyDetector(monitor)

    print("Simulating suspicious activity...\n")

    # Scenario 1: Multiple failed login attempts
    suspicious_user = "attacker"

    print(f"Scenario 1: Failed authentication attempts")
    for i in range(7):
        monitor.log_event(
            EventType.FAILED_AUTH,
            suspicious_user,
            f"Failed login attempt {i+1}",
            ip_address="203.0.113.42"
        )

    result = detector.detect_anomalies(suspicious_user, time_window=timedelta(hours=1))

    print(f"  Anomaly detected: {result.is_anomaly}")
    print(f"  Threat level: {result.threat_level.value}")
    print(f"  Confidence: {result.confidence:.2%}")
    print(f"  Reasons:")
    for reason in result.reasons:
        print(f"    - {reason}")
    if result.recommended_action:
        print(f"  Recommended action: {result.recommended_action}")
    print()

    # Scenario 2: SQL injection attempt
    print(f"Scenario 2: SQL injection attempt")
    monitor.log_query(
        "malicious_user",
        "SELECT * FROM users WHERE id = 1 OR '1'='1'",
        0.1,
        1000,
        True,
        ip_address="198.51.100.23"
    )

    result = detector.detect_anomalies("malicious_user", time_window=timedelta(hours=1))

    print(f"  Anomaly detected: {result.is_anomaly}")
    print(f"  Threat level: {result.threat_level.value}")
    print(f"  Reasons:")
    for reason in result.reasons:
        print(f"    - {reason}")
    print()

    # Scenario 3: High query rate
    print(f"Scenario 3: Unusual query rate")
    normal_user = "data_scientist"

    # Simulate high query rate
    for i in range(150):
        monitor.log_query(
            normal_user,
            f"SELECT * FROM data WHERE id = {i}",
            0.01,
            10,
            True
        )

    result = detector.detect_anomalies(normal_user, time_window=timedelta(minutes=1))

    print(f"  Anomaly detected: {result.is_anomaly}")
    print(f"  Threat level: {result.threat_level.value}")
    if result.reasons:
        print(f"  Reasons:")
        for reason in result.reasons:
            print(f"    - {reason}")
    print()

    # Get threat dashboard
    print("Security Threat Dashboard:")
    dashboard = detector.get_threat_dashboard()

    print(f"  Timestamp: {dashboard['timestamp']}")
    print(f"  High threat events (24h): {dashboard['high_threat_events_24h']}")
    print(f"  Active users: {dashboard['total_active_users']}")
    print(f"  Users with anomalies: {len(dashboard['users_with_anomalies'])}")

    if dashboard['users_with_anomalies']:
        print(f"\n  Alert: Suspicious activity detected:")
        for user_anomaly in dashboard['users_with_anomalies']:
            print(f"    - User: {user_anomaly['user_id']}")
            print(f"      Threat: {user_anomaly['threat_level']}")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("  Advanced Security Features Demo - v2.0.0")
    print("="*60)

    try:
        demo_two_factor_auth()
        demo_sso_integration()
        demo_certificate_auth()
        demo_activity_monitoring()
        demo_anomaly_detection()

        print_section("Demo Complete!")
        print("Security features demonstrated:")
        print("  ✓ Two-factor authentication (TOTP)")
        print("  ✓ SSO integration (OAuth 2.0, SAML)")
        print("  ✓ Certificate-based authentication")
        print("  ✓ Real-time activity monitoring")
        print("  ✓ Anomaly detection and threat assessment")
        print("\nFor production deployment:")
        print("  1. Install optional dependencies:")
        print("     pip install pyotp requests-oauthlib python3-saml")
        print("  2. Configure your SSO providers")
        print("  3. Set up certificate infrastructure")
        print("  4. Integrate with your authentication system")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
