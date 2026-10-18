# Identity and access management

> Khi tài nguyên chuyển lên cloud và SaaS, danh tính (identity) trở thành vành đai bảo mật mới: ai là ai, được làm gì, và có dấu hiệu bất thường không.

## Tại sao cần biết
Đa số xâm nhập hiện đại bắt đầu từ credential bị lộ hoặc lạm dụng. IAM là nhóm control quan trọng nhất và là nguồn log giá trị nhất cho phát hiện.

## Khái niệm cốt lõi

- **Identity**: người dùng, dịch vụ (service account), thiết bị, workload.
- **AAA**: *Authentication* (xác thực: bạn là ai), *Authorization* (cấp quyền: bạn được làm gì), *Accounting* (ghi lại bạn đã làm gì).
- **Yếu tố xác thực**: biết (mật khẩu), có (token, điện thoại), là (sinh trắc). **MFA** dùng từ hai yếu tố khác loại trở lên. MFA chống phishing tốt hơn khi dùng khóa phần cứng/FIDO2 thay vì SMS/OTP.
- **SSO** (Single Sign-On): đăng nhập một lần cho nhiều ứng dụng; giao thức phổ biến: SAML, OpenID Connect (trên OAuth 2.0). **OAuth 2.0** là khung ủy quyền (cấp token), không phải xác thực.
- **Directory**: kho danh tính tập trung, ví dụ Active Directory, Entra ID, LDAP. **Kerberos** là cơ chế xác thực vé trong AD.
- **Mô hình phân quyền**: **RBAC** (theo vai trò), **ABAC** (theo thuộc tính/ngữ cảnh). Nguyên tắc least privilege.
- **IGA / lifecycle**: Joiner–Mover–Leaver, rà soát quyền định kỳ (access review).
- **PAM** (Privileged Access Management): quản lý tài khoản đặc quyền (admin): vault mật khẩu, cấp quyền tạm thời (just-in-time), ghi lại phiên.
- **ITDR** (Identity Threat Detection & Response): phát hiện tấn công vào hạ tầng danh tính.

### Tấn công vào danh tính
Phishing lấy credential, password spray / credential stuffing, MFA fatigue (spam yêu cầu duyệt), đánh cắp token/session cookie, Kerberoasting, lạm dụng service account có quyền quá lớn.

## Cách hoạt động

Luồng SSO đơn giản hóa:
```
User → App: truy cập
App → IdP: chuyển hướng đăng nhập
User ↔ IdP: xác thực (mật khẩu + MFA)
IdP → App: trả assertion/token đã ký (SAML / OIDC)
App: kiểm tra chữ ký, tạo phiên, áp quyền
```
Mọi bước ghi log ở IdP (đăng nhập thành công/thất bại, thay đổi MFA, cấp quyền); đây là nguồn dữ liệu cho SIEM.

## Ví dụ
Dấu hiệu password spray: nhiều tài khoản khác nhau, mỗi tài khoản thất bại 1–2 lần, cùng một nguồn IP. Trên Windows, đăng nhập thất bại ghi event ID `4625`, thành công `4624`. Rule thống kê "một IP thất bại trên N tài khoản trong M phút" phát hiện được mẫu này mà ngưỡng "5 lần thất bại trên một tài khoản" bỏ sót.

## Hiểu nhầm thường gặp
- **"Có MFA là hết phishing"**: attacker dùng proxy đánh cắp session sau khi MFA xong, hoặc spam yêu cầu duyệt.
- **"OAuth là đăng nhập"**: OAuth cấp quyền truy cập; xác thực đi qua OpenID Connect.
- **Quên identity không phải con người**: service account và API key thường ít được giám sát và quyền lớn.

## Liên quan
- [05-defense-controls.md](05-defense-controls.md): các lớp control khác.
- [07-logging-and-telemetry.md](07-logging-and-telemetry.md): log danh tính đi vào hệ thống phát hiện.
